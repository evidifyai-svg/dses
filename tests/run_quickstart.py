#!/usr/bin/env python3
"""Positive and targeted negative tests for the external quickstart profile."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from verify_sequence import verify_document  # noqa: E402


def load(name: str) -> dict:
    return json.loads((ROOT / "quickstart" / name).read_text())


def expect_valid(name: str, document: dict) -> None:
    failures = verify_document(document, name=name)
    if failures:
        raise AssertionError(f"{name} should pass:\n" + "\n".join(failures))


def expect_rejected(name: str, document: dict, fragment: str) -> None:
    failures = verify_document(document, name=name)
    if not any(fragment in failure for failure in failures):
        raise AssertionError(
            f"{name} should fail with {fragment!r}; got:\n" + "\n".join(failures)
        )


def main() -> int:
    passive = load("passive-exposure.json")
    sealed = load("sealed-sequence.json")
    expect_valid("passive", passive)
    expect_valid("sealed", sealed)

    missing_model_version = copy.deepcopy(passive)
    del missing_model_version["events"][2]["ai_system"]["model_version"]
    expect_rejected("missing model version", missing_model_version, "model_version")

    wrong_information_state = copy.deepcopy(sealed)
    wrong_information_state["events"][2]["information_state"]["independence_class"] = "DIRECTLY_EXPOSED"
    expect_rejected("inflated independence", wrong_information_state, "independence_class")

    wrong_hash = copy.deepcopy(sealed)
    wrong_hash["events"][4]["integrity"]["event_hash"] = "f" * 64
    expect_rejected("wrong event hash", wrong_hash, "event_hash does not match")

    wrong_payload = copy.deepcopy(sealed)
    first_ref = next(iter(wrong_payload["disclosed_payloads"]))
    wrong_payload["disclosed_payloads"][first_ref]["finding"] = "positive"
    expect_rejected("wrong disclosed payload", wrong_payload, "does not recompute")

    exposure_before_state = copy.deepcopy(sealed)
    exposure_before_state["events"][2], exposure_before_state["events"][3] = (
        exposure_before_state["events"][3], exposure_before_state["events"][2]
    )
    expect_rejected("exposure before state", exposure_before_state, "contiguous sequence order")

    malformed_nested_object = copy.deepcopy(passive)
    malformed_nested_object["events"][2]["integrity"] = "I1"
    expect_rejected("malformed nested object", malformed_nested_object, "not of type 'object'")

    print("quickstart tests: 2 valid examples passed; 6 targeted mutations rejected")
    print("quickstart tests make no conformance claim")
    return 0


if __name__ == "__main__":
    sys.exit(main())
