#!/usr/bin/env python3
"""Verify the DSES v0.1 quickstart sequence profile.

Passing this tool establishes only the checks it reports. It does not register
or create a DSES Conformant claim. The outcome-layer conformance gate remains
scripts/dses_verify.py plus the process in CONFORMANCE-POLICY.md.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
from pathlib import Path

import jcs
from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "dses-v0.1.schema.json"
CLASS_RANK = {"I0": 0, "I1": 1, "I2": 2, "I3": 3}
DIRECT = {"CATEGORICAL", "LOCALIZATION", "QUANTITATIVE", "NARRATIVE", "DIRECTIVE"}
SHA256_REF = re.compile(r"^sha256:[0-9a-f]{64}$")
SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")
STATE_EVENTS = {"human_state_committed", "human_state_revised", "final_decision_committed"}


def canonical_digest(value: object) -> str:
    return hashlib.sha256(jcs.canonicalize(value)).hexdigest()


def event_digest(event: dict) -> str:
    preimage = copy.deepcopy(event)
    preimage["integrity"].pop("event_hash", None)
    return canonical_digest(preimage)


def independence_for(classes: set[str]) -> str:
    if "AGENTIC" in classes:
        return "POST_ACTION"
    if classes & DIRECT:
        return "DIRECTLY_EXPOSED"
    if classes:
        return "INDIRECTLY_EXPOSED"
    return "UNEXPOSED"


def as_object(value: object) -> dict:
    return value if isinstance(value, dict) else {}


def string_set(value: object) -> set[str]:
    return {item for item in value if isinstance(item, str)} if isinstance(value, list) else set()


def ai_identity(event: dict) -> tuple[str, ...]:
    ai = as_object(event.get("ai_system"))
    values = (ai.get("name"), ai.get("model_id"), ai.get("model_version"), ai.get("deployment_id"))
    return tuple(json.dumps(value, sort_keys=True) for value in values)


def verify_document(document: dict, *, name: str = "sequence") -> list[str]:
    errors: list[str] = []

    if document.get("dses_version") != "0.1.0":
        errors.append(f"{name}: dses_version must be 0.1.0 for this quickstart profile")

    scope = document.get("example_scope")
    if not isinstance(scope, dict):
        errors.append(f"{name}: example_scope is required")
        scope = {}
    level = scope.get("capture_level")
    declared_class = scope.get("integrity_class")
    if not isinstance(level, str) or level not in {"L1", "L2", "L3"}:
        errors.append(f"{name}: example_scope.capture_level must be L1, L2, or L3")
    if not isinstance(declared_class, str) or declared_class not in CLASS_RANK:
        errors.append(f"{name}: example_scope.integrity_class must be I0, I1, I2, or I3")

    events = document.get("events")
    if not isinstance(events, list) or not events:
        return errors + [f"{name}: events must be a non-empty array"]

    schema = json.loads(SCHEMA_PATH.read_text())
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    for index, event in enumerate(events):
        for failure in sorted(validator.iter_errors(event), key=lambda item: list(item.path)):
            path = ".".join(str(part) for part in failure.path) or "<event>"
            errors.append(f"{name}: event[{index}] {path}: {failure.message}")

    if any(not isinstance(event, dict) for event in events):
        return errors

    ids = [event.get("event_id") for event in events]
    comparable_ids = [json.dumps(value, sort_keys=True) for value in ids]
    if len(ids) != len(set(comparable_ids)):
        errors.append(f"{name}: event_id values must be unique")

    sequences = [event.get("sequence") for event in events]
    if sequences != list(range(len(events))):
        errors.append(f"{name}: events must be stored in contiguous sequence order starting at zero")

    case_refs = {json.dumps(event.get("case_ref"), sort_keys=True) for event in events}
    if len(case_refs) != 1:
        errors.append(f"{name}: one quickstart file must contain exactly one case_ref")

    if events[0].get("event_type") != "case_context_created":
        errors.append(f"{name}: the first event must be case_context_created")
    finals = [index for index, event in enumerate(events) if event.get("event_type") == "final_decision_committed"]
    if finals != [len(events) - 1]:
        errors.append(f"{name}: exactly one final_decision_committed must terminate the sequence")

    event_classes = [as_object(event.get("integrity")).get("class") for event in events]
    if (
        all(isinstance(value, str) and value in CLASS_RANK for value in event_classes)
        and isinstance(declared_class, str)
        and declared_class in CLASS_RANK
    ):
        minimum = min(event_classes, key=CLASS_RANK.get)
        if CLASS_RANK[declared_class] > CLASS_RANK[minimum]:
            errors.append(
                f"{name}: declared {declared_class} exceeds the minimum event integrity class {minimum}"
            )

    disclosed = document.get("disclosed_payloads", {})
    if not isinstance(disclosed, dict):
        errors.append(f"{name}: disclosed_payloads must be an object when supplied")
        disclosed = {}
    for reference, payload in disclosed.items():
        expected = "sha256:" + canonical_digest(payload)
        if reference != expected:
            errors.append(f"{name}: disclosed payload commitment {reference} does not recompute")

    available: set[tuple[str, ...]] = set()
    exposure_by_actor: dict[str, set[str]] = {}
    earlier_states: set[str] = set()
    human_state_indices: list[int] = []
    presentation_indices: list[int] = []
    revision_indices: list[int] = []

    previous_hash = "GENESIS"
    for index, event in enumerate(events):
        event_type = event.get("event_type")
        integrity = as_object(event.get("integrity"))
        integrity_class = integrity.get("class")

        if isinstance(integrity_class, str) and integrity_class in {"I2", "I3"}:
            stored = integrity.get("event_hash")
            if not isinstance(stored, str) or not SHA256_HEX.fullmatch(stored):
                errors.append(f"{name}: event[{index}] requires a full lowercase SHA-256 event_hash")
            else:
                try:
                    matches = stored == event_digest(event)
                except (TypeError, ValueError, OverflowError) as exc:
                    errors.append(f"{name}: event[{index}] event hash preimage cannot be canonicalized: {exc}")
                else:
                    if not matches:
                        errors.append(f"{name}: event[{index}] event_hash does not match its RFC 8785 preimage")
            if integrity.get("prev_event_hash") != previous_hash:
                errors.append(f"{name}: event[{index}] prev_event_hash does not match its predecessor")
            if integrity.get("canonicalization") != "RFC8785" or integrity.get("hash_alg") != "SHA-256":
                errors.append(f"{name}: event[{index}] I2+ quickstart events must declare RFC8785 and SHA-256")
            if isinstance(stored, str):
                previous_hash = stored

        if event_type == "ai_result_available":
            available.add(ai_identity(event))

        if event_type == "context_signal_recorded" and event.get("exposure"):
            actor = as_object(event.get("actor"))
            actor_ref = actor.get("actor_ref")
            if actor.get("actor_type") != "human" or not isinstance(actor_ref, str) or not actor_ref:
                errors.append(
                    f"{name}: event[{index}] quickstart context exposure must identify the human recipient"
                )
            else:
                exposure_by_actor.setdefault(actor_ref, set()).update(
                    string_set(as_object(event.get("exposure")).get("classes"))
                )

        if event_type == "ai_result_presented":
            presentation_indices.append(index)
            if ai_identity(event) not in available:
                errors.append(f"{name}: event[{index}] presents an AI result not previously recorded as available")
            actor = as_object(event.get("actor"))
            if actor.get("actor_type") != "human":
                errors.append(f"{name}: event[{index}] ai_result_presented must identify the human recipient")
            actor_ref = actor.get("actor_ref")
            if isinstance(actor_ref, str) and actor_ref:
                exposure_by_actor.setdefault(actor_ref, set()).update(
                    string_set(as_object(event.get("exposure")).get("classes"))
                )
            if isinstance(integrity_class, str) and integrity_class in {"I2", "I3"}:
                commitment = as_object(event.get("exposure")).get("payload_commitment")
                if not isinstance(commitment, str) or not SHA256_REF.fullmatch(commitment):
                    errors.append(f"{name}: event[{index}] I2+ presentation needs a sha256: payload_commitment")
                elif commitment not in disclosed:
                    errors.append(f"{name}: event[{index}] quickstart payload commitment is not disclosed")

        if event_type == "ai_result_interacted" and event.get("exposure"):
            actor = as_object(event.get("actor"))
            actor_ref = actor.get("actor_ref")
            if actor.get("actor_type") != "human" or not isinstance(actor_ref, str) or not actor_ref:
                errors.append(f"{name}: event[{index}] AI interaction must identify the human recipient")
            else:
                exposure_by_actor.setdefault(actor_ref, set()).update(
                    string_set(as_object(event.get("exposure")).get("classes"))
                )

        if isinstance(event_type, str) and event_type in STATE_EVENTS:
            actor_ref = as_object(event.get("actor")).get("actor_ref")
            expected_classes = exposure_by_actor.get(actor_ref, set()) if isinstance(actor_ref, str) else set()
            information = as_object(event.get("information_state"))
            actual_classes = string_set(information.get("exposure_classes"))
            if actual_classes != expected_classes:
                errors.append(f"{name}: event[{index}] information-state exposure classes do not match prior presentation")
            expected_independence = independence_for(expected_classes)
            if information.get("independence_class") != expected_independence:
                errors.append(f"{name}: event[{index}] independence_class must be {expected_independence}")

            state_ref = event.get("decision_state_ref")
            if isinstance(integrity_class, str) and integrity_class in {"I2", "I3"}:
                if not isinstance(state_ref, str) or not SHA256_REF.fullmatch(state_ref):
                    errors.append(f"{name}: event[{index}] I2+ decision state needs a sha256: reference")
                elif state_ref not in disclosed:
                    errors.append(f"{name}: event[{index}] quickstart decision state is not disclosed")

            if event_type == "human_state_committed":
                human_state_indices.append(index)
            if event_type == "human_state_revised":
                revision_indices.append(index)
                if event.get("prior_decision_state_ref") not in earlier_states:
                    errors.append(f"{name}: event[{index}] prior_decision_state_ref does not name an earlier state")
            if isinstance(state_ref, str):
                earlier_states.add(state_ref)

    if isinstance(level, str) and level in {"L2", "L3"}:
        if not human_state_indices or not presentation_indices or not revision_indices:
            errors.append(f"{name}: the quickstart L2/L3 profile requires pre-state, presentation, and revision events")
        elif not (human_state_indices[0] < presentation_indices[0] < revision_indices[0]):
            errors.append(f"{name}: L2/L3 quickstart ordering must be pre-state, presentation, then revision")

    if level == "L3":
        if declared_class != "I3":
            errors.append(f"{name}: the quickstart L3 profile must declare I3")
        enforced = any(as_object(event.get("integrity")).get("enforcement") for event in events)
        if not enforced:
            errors.append(f"{name}: L3 requires documented enforcement evidence")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify DSES v0.1 quickstart sequences without creating a conformance claim."
    )
    parser.add_argument("files", nargs="+", type=Path)
    args = parser.parse_args()

    failures = 0
    for path in args.files:
        try:
            document = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError) as exc:
            print(f"FAIL {path}: {exc}")
            failures += 1
            continue
        errors = verify_document(document, name=str(path))
        if errors:
            print(f"FAIL {path}: {len(errors)} problem(s)")
            for error in errors:
                print(f"  - {error}")
            failures += 1
        else:
            scope = document["example_scope"]
            note = "internal consistency only; no external anchor" if scope["integrity_class"] == "I2" else "operator-attributable record"
            print(
                f"PASS {path}: {len(document['events'])} events, "
                f"{scope['capture_level']}/{scope['integrity_class']}; {note}"
            )

    print(f"\nquickstart verification: {len(args.files) - failures} passed, {failures} failed")
    print("This result is not a DSES Conformant registration or certificate.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
