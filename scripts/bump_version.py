#!/usr/bin/env python3
"""Move the candidate label everywhere it is normative, and nowhere it is history.

    python3 scripts/bump_version.py <label>

The current label is read from the **Version:** line of DSES-v0.2.md. Every
exact occurrence of it (with or without a leading v) is rewritten in the files
listed below. Annex C of the specification is left alone, because a changelog
that no longer names the candidate it describes is not a changelog. Prose that
names an older candidate by bare suffix ("rc9 disclosed", "what changes in
rc10") is history and is not touched: only the exact dotted label moves.

The target label may be a candidate (an -rcN suffix) or a permanent release
(no suffix). Dropping the suffix is the mint, and it is not a quiet change:
release_lint.py L8 refuses a non-candidate build while the specification still
says REVIEW-SYSTEM-UNSPECIFIED, so a mint fails the gate until named review
provenance is resolved. That refusal is the point. Run the bump only when the
review disclosure is ready to change with it.

After bumping: regenerate the worked example (its package label embeds the
version, so its hashes change), then run the gate. release_lint.py L9 checks
that no file below still carries a stale label, and L12 checks that no shipped
file carries a label this script does not own.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC = os.path.join(ROOT, "DSES-v0.2.md")

# Every file that states the current candidate. release_lint.py L9 reads this
# list, so a file added here is a file the lint will police.
VERSIONED = [
    "DSES-v0.2.md", "CLAIMS-CLASSIFICATION.md", "README.md", "IMPLEMENT.md",
    "CITATION.cff", ".zenodo.json", "run_all.sh", "requirements.txt",
    "schemas/dses-v0.2-definitions.schema.json", "schemas/dses-v0.2-derived.schema.json",
    "schemas/dses-v0.2-nonce-sidecar.schema.json", "schemas/dses-v0.2-outcome-events.schema.json",
    "schemas/dses-v0.2-package.schema.json",
    "scripts/dses_core.py", "scripts/generate_example.py", "scripts/make_release.py",
    "tests/run_regression.py", "site/index.html",
]
# Files that legitimately name an older candidate and are never rewritten.
HISTORY = ["ENVIRONMENTS.md", "ERRATA-v0.1.md"]
# Files that carry the label but are rebuilt by tooling rather than rewritten
# here. The worked example embeds the label in its package name and is minted by
# generate_example.py; release_lint L9 checks it directly against the spec's
# Version line, so it is managed, just not by this script.
REGENERATED = ["examples/example-package.json"]
# Files whose sha256 is registered INSIDE the worked example. Their identity is
# their digest, so a bump cannot rewrite them: changing one byte of a docstring
# breaks the package's DRV-ENGINE binding and the shipped example stops
# verifying. Their label is therefore frozen at the candidate in which the
# engine itself last changed, which is a fact about content addressing and not
# a stale string. release_lint L12 checks the digest is still the registered
# one, so an edit here fails as a named invariant instead of as seven opaque
# verifier failures.
DIGEST_BOUND = ["scripts/dses_derivation.py"]
CHANGELOG_HEADING = "## Annex C: Changelog"
LABEL = re.compile(r"\b(\d+\.\d+\.\d+(?:-rc\d+)?)\b")


def current_label():
    m = re.search(r"\*\*Version:\*\*\s*(\S+)", open(SPEC, encoding="utf8").read())
    if not m:
        raise SystemExit("bump: no **Version:** line in DSES-v0.2.md")
    return m.group(1)


def rewrite(text, old, new, protect_changelog=False):
    if protect_changelog and CHANGELOG_HEADING in text:
        head, tail = text.split(CHANGELOG_HEADING, 1)
        # Annex D and E follow the changelog; only Annex C itself is protected.
        parts = re.split(r"(?m)^(?=## Annex [D-Z])", tail, maxsplit=1)
        annex_c, rest = parts[0], (parts[1] if len(parts) > 1 else "")
        return head.replace(old, new) + CHANGELOG_HEADING + annex_c + rest.replace(old, new)
    return text.replace(old, new)


def main():
    if len(sys.argv) != 2 or not LABEL.fullmatch(sys.argv[1]):
        raise SystemExit(__doc__)
    new = sys.argv[1]
    old = current_label()
    if old == new:
        print(f"bump: already at {new}")
        return 0
    changed = 0
    for rel in VERSIONED:
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            continue
        src = open(p, encoding="utf8").read()
        out = rewrite(src, old, new, protect_changelog=(rel == "DSES-v0.2.md"))
        if out != src:
            open(p, "w", encoding="utf8").write(out)
            changed += 1
            print(f"bump: {rel}  {src.count(old) - out.count(old)} occurrence(s)")
    print(f"bump: {old} -> {new} in {changed} file(s); now regenerate the example and run the gate")
    return 0


if __name__ == "__main__":
    sys.exit(main())
