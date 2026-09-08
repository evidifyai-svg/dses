#!/usr/bin/env python3
"""Normative-coherence check: prose vocabulary agrees with the schemas.

Every event-shaped identifier that appears in shipped prose (the markdown
allowlist plus `description` and `title` strings inside the schemas) must
exist in the schema vocabulary: an event_type value, an enum value, or a
property name. The rc10 archive shipped one leftover, `artifact_anchored`,
in a schema description, contradicting the event actually named in the
specification. This check makes that class of drift a gate failure.

"Event-shaped" means: a snake_case token whose final segment is the final
segment of some event_type value (recorded, committed, revised, declared,
superseded, invalidated, observed, adjudicated, ...). Other snake_case tokens
are field names and are checked only when they look like a field
(`backticked` in markdown) and are absent from the vocabulary.

Exit 1 on any finding. `--list` prints the derived vocabulary.
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMAS = sorted(glob.glob(os.path.join(ROOT, "schemas", "*.json"))) + [os.path.join(ROOT, "dses-v0.1.schema.json")]
PROSE = [
    "DSES-v0.1.md", "DSES-v0.2.md", "ERRATA-v0.1.md", "CLAIMS-CLASSIFICATION.md",
    "README.md", "IMPLEMENT.md", "IMPLEMENTATION-CHECKLIST.md", "FOUNDING-IMPLEMENTERS.md",
    "CONFORMANCE-POLICY.md", "SCORECARD.md", "ENVIRONMENTS.md", "RELIANCE-CONTEXT-EXAMPLE.md",
    "GOVERNANCE.md", "SECURITY.md", "CONTRIBUTING.md",
    "TERMINOLOGY.md", "CLAIM-LEDGER.md", "ERRATA-v0.2.md",
]
TOKEN = re.compile(r"(?<![A-Za-z0-9_./-])[a-z][a-z0-9]*(?:_[a-z0-9]+)+(?![A-Za-z0-9_])")
ALLOW_PATH = os.path.join(ROOT, "scripts", "vocabulary-allow.json")


def walk(o, vocab, descs, path):
    if isinstance(o, dict):
        c = o.get("const")
        if isinstance(c, str):
            vocab.add(c)
        for e in o.get("enum") or []:
            if isinstance(e, str):
                vocab.add(e)
        for k in (o.get("properties") or {}):
            vocab.add(k)
        # Names a schema requires or prohibits (required lists, including those
        # under `not`) are schema vocabulary too: the prose may name a
        # prohibited key when explaining why it is prohibited.
        for k in (o.get("required") or []):
            if isinstance(k, str):
                vocab.add(k)
        for k in ("description", "title"):
            if isinstance(o.get(k), str):
                descs.append((path, o[k]))
        for k, v in o.items():
            walk(v, vocab, descs, path)
    elif isinstance(o, list):
        for v in o:
            walk(v, vocab, descs, path)


def main():
    vocab, descs = set(), []
    for s in SCHEMAS:
        walk(json.load(open(s)), vocab, descs, os.path.relpath(s, ROOT))
    event_types = set()
    for s in SCHEMAS:
        for m in re.finditer(r'"event_type"\s*:\s*\{[^}]*?"(?:enum|const)"\s*:\s*(\[[^\]]*\]|"[^"]+")', open(s).read(), re.S):
            body = m.group(1)
            event_types.update(re.findall(r'"([a-z_]+)"', body))
    # v0.1 event types live under a differently named key; take every enum value
    # that ends in a recognized verb participle as an event as well.
    suffixes = {e.rsplit("_", 1)[-1] for e in event_types} | {"recorded", "committed", "revised", "declared", "superseded", "invalidated", "observed", "adjudicated", "anchored"}
    allow = set()
    if os.path.exists(ALLOW_PATH):
        allow = {a["token"] for a in json.load(open(ALLOW_PATH)).get("allow", [])}

    if "--list" in sys.argv:
        print("\n".join(sorted(vocab)))
        return 0

    findings = []

    def check(where, text, backtick_only, resolves):
        for m in TOKEN.finditer(text):
            tok = m.group(0)
            event_shaped = tok.rsplit("_", 1)[-1] in suffixes
            if resolves(tok, event_shaped):
                continue
            if event_shaped:
                findings.append((where, tok, "event-shaped identifier absent from schema vocabulary"))
            elif backtick_only:
                a, b = m.start(), m.end()
                if a > 0 and text[a - 1] == "`" and b < len(text) and text[b] == "`":
                    findings.append((where, tok, "backticked identifier absent from schema vocabulary"))

    # Implementation vocabulary: identifiers the reference implementation uses
    # (report fields, module names, status labels). A backticked field-shaped
    # token may resolve here. An event-shaped token may NOT: events are schema
    # vocabulary or they are drift.
    impl = set()
    for f in sorted(glob.glob(os.path.join(ROOT, "scripts", "*.py"))) + sorted(glob.glob(os.path.join(ROOT, "rules", "*.py"))):
        impl.update(TOKEN.findall(open(f, encoding="utf8").read()))

    def resolves(tok, event_shaped):
        return tok in vocab or tok in allow or (not event_shaped and tok in impl)

    for path, text in descs:
        check(path, text, backtick_only=False, resolves=resolves)
    for name in PROSE:
        p = os.path.join(ROOT, name)
        if not os.path.exists(p):
            continue
        in_changelog = False
        for i, line in enumerate(open(p, encoding="utf8"), 1):
            # Annex C records what earlier candidates called things. History
            # legitimately names retired vocabulary and is not checked.
            if line.startswith("## Annex C"):
                in_changelog = True
            elif line.startswith("## "):
                in_changelog = False
            if in_changelog:
                continue
            check(f"{name}:{i}", line, backtick_only=True, resolves=resolves)

    for where, tok, why in findings:
        print(f"VOCAB  {where}  {tok}  {why}")
    print(f"vocabulary check: {len(vocab)} schema terms, {len(findings)} finding(s)")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
