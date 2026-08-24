#!/usr/bin/env python3
"""Layer one of conformance: JSON Schema validation of every object in a package.

Layer two is scripts/dses_verify.py. Neither is sufficient alone (Section 10).
"""
import json
import os
import sys

from jsonschema import Draft202012Validator

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(name):
    return json.load(open(os.path.join(ROOT, "schemas", name)))


def main(package=None, artifacts_dir=None, derived_dir=None, quiet=False):
    env = Draft202012Validator(load("dses-v0.2-package.schema.json"))
    ev = Draft202012Validator(load("dses-v0.2-outcome-events.schema.json"))
    dfn = Draft202012Validator(load("dses-v0.2-definitions.schema.json"))
    drv = Draft202012Validator(load("dses-v0.2-derived.schema.json"))
    for v in (env, ev, dfn, drv):
        Draft202012Validator.check_schema(v.schema)

    pkg = json.load(open(package or os.path.join(ROOT, "examples", "example-package.json")))
    errors = []
    n = 1
    for err in env.iter_errors(pkg):
        errors.append(f"package envelope: {list(err.absolute_path)}: {err.message[:160]}")
    for ch in [pkg["cohort_chain"]] + pkg["case_chains"]:
        for e in ch:
            n += 1
            for err in ev.iter_errors(e):
                errors.append(f"event {e['event_id']}: {list(err.absolute_path)}: {err.message[:160]}")
    adir = artifacts_dir or os.path.join(ROOT, "artifacts")
    for fn in sorted(os.listdir(adir)):
        n += 1
        for err in dfn.iter_errors(json.load(open(os.path.join(adir, fn)))):
            errors.append(f"artifact {fn}: {list(err.absolute_path)}: {err.message[:160]}")
    ddir = derived_dir or os.path.join(ROOT, "examples", "derived")
    for fn in sorted(os.listdir(ddir)):
        if not fn.endswith(".json"):
            continue
        n += 1
        for err in drv.iter_errors(json.load(open(os.path.join(ddir, fn)))):
            errors.append(f"derived {fn}: {list(err.absolute_path)}: {err.message[:160]}")

    ns = os.path.join(ROOT, "examples", "nonce-store.json")
    if os.path.exists(ns):
        nsv = Draft202012Validator(load("dses-v0.2-nonce-sidecar.schema.json"))
        n += 1
        for err in nsv.iter_errors(json.load(open(ns))):
            errors.append(f"nonce sidecar: {list(err.absolute_path)}: {err.message[:160]}")

    sdir = os.path.join(ROOT, "examples", "decision-sequences")
    for fn in (sorted(os.listdir(sdir)) if os.path.isdir(sdir) else []):
        seq = json.load(open(os.path.join(sdir, fn)))
        for e in seq["events"]:
            n += 1
            for k in ("event_id", "event_type", "sequence", "payload_commitment", "integrity", "payload"):
                if k not in e:
                    errors.append(f"v0.1 {fn}/{e.get('event_id','?')}: missing {k}")

    if not quiet:
        print(f"schema validation: {n} objects, {len(errors)} errors")
        for e in errors:
            print(f"  {e}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
