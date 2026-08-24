#!/usr/bin/env python3
"""ENVIRONMENTS.md carries the gate counts it claims.

rc10 shipped an ENVIRONMENTS.md whose Environment B record stated 199 objects,
2027 checks, 113 adversarial cases and 68 manifest entries against a gate that
produced 206, 2286, 158 and 101. Hand-typed counts drift; this specification
exists to make drift of that kind a failure, so the counts block is now
machine-written from the gate log and machine-checked on every run.

    python3 scripts/check_environments.py GATE_LOG            check (gate step 7)
    python3 scripts/check_environments.py GATE_LOG --write    rewrite the block

The block is delimited by <!-- gate-counts:begin --> and <!-- gate-counts:end -->.
Per-environment records below it state interpreter and dependency facts and the
candidate at which the gate was last observed green there. They carry no counts.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV = os.path.join(ROOT, "ENVIRONMENTS.md")
MANIFEST = os.path.join(ROOT, "RELEASE-MANIFEST.sha256")
BEGIN, END = "<!-- gate-counts:begin -->", "<!-- gate-counts:end -->"

PATTERNS = {
    "vectors": r"canonicalization self-test: (\d+) vectors passed",
    "lint": r"release lint: (\d+) problems",
    "objects": r"schema validation: (\d+) objects, (\d+) errors",
    "checks": r"(\d+) checks, (\d+) failures",
    "profile": r"^(OL CONFORMANT|OL NONCONFORMANT)\s*$",
    "adversarial": r"(\d+) adversarial cases, (\d+) rejected at the asserted rule, (\d+) not",
    "quickstart": r"quickstart tests: (\d+) valid examples passed; (\d+) targeted mutations rejected",
    "vocabulary": r"vocabulary check: (\d+) schema terms, (\d+) finding\(s\)",
}


def parse(log):
    got = {}
    for key, pat in PATTERNS.items():
        # The regeneration step (6) re-prints validation and verifier lines for
        # the temporary tree; the first match is the shipped tree.
        m = re.search(pat, log, re.M)
        if not m:
            raise SystemExit(f"environment check: gate log has no line matching {key!r}")
        got[key] = m.groups()
    manifest_entries = sum(1 for line in open(MANIFEST) if line.strip()) if os.path.exists(MANIFEST) else 0
    o, oe = got["objects"]
    c, cf = got["checks"]
    a, ar, an = got["adversarial"]
    q, qm = got["quickstart"]
    vt, vf = got["vocabulary"]
    lines = [
        f"- RFC 8785 canonicalization self-test: {got['vectors'][0]}/{got['vectors'][0]} vectors",
        f"- release lint: {got['lint'][0]} problems",
        f"- schema validation of shipped artifacts: {o} objects, {oe} errors",
        f"- semantic-cryptographic verifier: {c} checks, {cf} failures, {got['profile'][0]}",
        f"- adversarial suite: {a} cases, {ar} rejected at the asserted rule, {an} not",
        f"- quickstart: {q} valid examples passed, {qm} targeted mutations rejected",
        f"- vocabulary check: {vt} schema terms, {vf} findings",
        f"- release manifest: {manifest_entries} entries",
    ]
    return "\n".join(lines)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    write = "--write" in sys.argv
    if not args:
        raise SystemExit(__doc__)
    log = open(args[0], encoding="utf8", errors="replace").read()
    want = parse(log)
    src = open(ENV, encoding="utf8").read()
    if BEGIN not in src or END not in src:
        raise SystemExit("environment check: ENVIRONMENTS.md has no gate-counts block")
    head, rest = src.split(BEGIN, 1)
    _, tail = rest.split(END, 1)
    have = rest.split(END, 1)[0].strip()
    if have == want:
        print("environment record: gate counts agree with ENVIRONMENTS.md")
        return 0
    if write:
        open(ENV, "w", encoding="utf8").write(f"{head}{BEGIN}\n{want}\n{END}{tail}")
        print("environment record: gate counts block rewritten from the gate log")
        return 0
    print("environment record: ENVIRONMENTS.md gate counts are STALE")
    print("--- recorded")
    print(have)
    print("--- gate log")
    print(want)
    print("rerun with --write after confirming the gate log is the shipped tree's")
    return 1


if __name__ == "__main__":
    sys.exit(main())
