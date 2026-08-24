#!/usr/bin/env python3
"""release_lint.py: make DSES submit to its own evidentiary rules.

Protocol Invariant 5 says no prose claims the verifier establishes something
until a check AND a fixture exist for it. CLAIMS-CLASSIFICATION defines
"implemented" the same strong way. Those are promises about this repository,
so they are machine-checked here rather than asserted in prose.

Checks performed:

  L1  Every rule identifier named in an `implemented` claims row exists in the
      reference verifier.
  L2  Every rule identifier named in an `implemented` claims row is asserted by
      at least one regression fixture.
  L3  Every rule identifier the verifier can emit appears in the claims table
      (no undocumented checks).
  L4  Every requirement row carries both a verification class and a support
      status.
  L5  Every uppercase conformance keyword in the specification carries one or
      more explicit ``<!-- req:ID -->`` tags, and every tag resolves to the
      claims table (no silently unclassified MUST/REQUIRED).
  L6  Numeric section numbers in the specification are unique and ascending.
  L7  Counts printed in CLAIMS-CLASSIFICATION and in the specification's Annex D
      match the counts recomputed from the rows.
  L8  Literal verifier rule/class pairs agree with the verification class(es)
      assigned to that rule in CLAIMS-CLASSIFICATION.

--emit-counts prints the recomputed inventory so the numbers are generated,
never typed.

Exit 0 only if every check passes.
"""
import argparse
import ast
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLAIMS = os.path.join(ROOT, "CLAIMS-CLASSIFICATION.md")
SPEC = os.path.join(ROOT, "DSES-v0.2.md")
VERIFIER = os.path.join(ROOT, "scripts", "dses_verify.py")
REGRESSION = os.path.join(ROOT, "tests", "run_regression.py")

RULE_RE = re.compile(r"\b([A-Z][A-Z0-9]{1,7}(?:-[A-Z0-9]{2,12})+)\b")
NORMATIVE = re.compile(r"\b(MUST NOT|MUST|REQUIRED|SHALL NOT|SHALL)\b")
NON_RULE = {"DSES-SIG", "DSES-ANCHOR", "RFC-8785", "CC-BY", "HMAC-SHA256"}


def parse_rows():
    """Each claims row: | id | requirement | rule | class | support |."""
    rows, section = [], None
    for line in open(CLAIMS):
        if line.startswith("## "):
            section = line.strip("# \n")
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 5 or cells[0] in ("#", "Class", "Status", "---"):
            continue
        if set(cells[0]) <= set("-: "):
            continue
        rid, req, rule, cls, support = cells
        if not re.match(r"^\d", rid):
            continue
        rows.append({"id": rid, "requirement": req, "rule": rule, "class": cls,
                     "support": support, "section": section})
    return rows


def row_rules(row):
    if row["rule"].strip().lower() in ("none", "schema", "prose", ""):
        return []
    out = []
    for tok in RULE_RE.findall(row["rule"]):
        if tok not in NON_RULE and "-" in tok:
            out.append(tok)
    return out


def row_classes(row):
    return [c.strip() for c in re.split(r"[+/]", re.sub(r"\*", "", row["class"])) if c.strip()]


def row_support(row):
    s = row["support"].lower()
    for k in ("not_implemented", "not applicable", "out of scope", "partial", "implemented"):
        if k in s:
            return k
    return "unknown"



def check_changelog_counts(problems):
    import re, subprocess
    spec = open(os.path.join(ROOT, "DSES-v0.2.md")).read()
    # scope to the NEWEST changelog entry only: a global search would bind to an
    # older entry's count when the newest omits the claim, reporting the wrong
    # failure (found while negative-testing the missing-claim branch)
    entries = re.split(r"\n\*\*0\.2\.0-", spec.split("## Annex C", 1)[-1])
    newest = entries[1] if len(entries) > 1 else ""
    m = re.search(r"suite stands at (\d+)", newest)
    t = open(os.path.join(ROOT, "tests", "run_regression.py")).read()
    actual = len(re.findall(r"^@case\(", t, re.M))
    if m is None:
        problems.append("L11 Annex C carries no 'suite stands at N' claim to check; "
                        "the newest changelog entry must state the suite count so it can be verified")
    elif int(m.group(1)) != actual:
        problems.append(f"L11 Annex C claims a suite of {m.group(1)} but tests/run_regression.py defines {actual} cases")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--emit-counts", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()

    rows = parse_rows()
    verifier_src = open(VERIFIER).read()
    regression_src = open(REGRESSION).read()
    spec_src = open(SPEC).read()

    verifier_rules = {t for t in RULE_RE.findall(verifier_src)
                      if f'"{t}")' in verifier_src or f'"{t}",' in verifier_src
                      or f'rule = "{t}"' in verifier_src}
    verifier_rules = {t for t in verifier_rules if t not in NON_RULE}
    asserted = set(re.findall(r'verifier_rejects\([^,]+,\s*"([A-Z0-9-]+)"', regression_src))
    problems = []

    # L1 / L2
    for row in rows:
        if row_support(row) != "implemented":
            continue
        for rule in row_rules(row):
            if rule not in verifier_rules:
                problems.append(f"L1 {row['id']}: rule {rule} is not emitted by the verifier")
            if rule not in asserted:
                problems.append(f"L2 {row['id']}: rule {rule} has no regression fixture asserting it, "
                                f"so 'implemented' is not earned")

    # L3
    documented = {r for row in rows for r in row_rules(row)}
    for rule in sorted(verifier_rules - documented - {"GEN"}):
        problems.append(f"L3 {rule}: verifier emits a rule the claims table does not document")

    # L4
    for row in rows:
        if not row_classes(row) or row_support(row) == "unknown":
            problems.append(f"L4 {row['id']}: missing verification class or support status")

    # L5: explicit normative traceability. A normative line without a tag is a
    # release failure; a tag that does not resolve is equally bad.
    covered = {row["id"] for row in rows}
    tag_re = re.compile(r"req:(\d+(?:\.\d+)*(?:[a-z])?)")
    spec_sections = re.findall(r"^#{2,4}\s+(?:Section\s+)?(\d+(?:\.\d+)*)", spec_src, re.M)
    for lineno, line in enumerate(spec_src.splitlines(), 1):
        if not NORMATIVE.search(line):
            continue
        if line.startswith(">") or line.strip().startswith("|"):
            continue
        ids = tag_re.findall(line)
        if not ids:
            problems.append(f"L5 line {lineno}: normative keyword has no <!-- req:ID --> tag")
            continue
        for rid in ids:
            if rid not in covered:
                problems.append(f"L5 line {lineno}: requirement tag {rid} is absent from CLAIMS-CLASSIFICATION")

    # Also reject orphan tags even on lines that no longer contain a keyword.
    for lineno, line in enumerate(spec_src.splitlines(), 1):
        for rid in tag_re.findall(line):
            if rid not in covered:
                problems.append(f"L5 line {lineno}: orphan requirement tag {rid}")

    # L6
    nums = [tuple(int(x) for x in s.split(".")) for s in spec_sections]
    seen = set()
    for i, n in enumerate(nums):
        if n in seen:
            problems.append(f"L6 duplicate section number {'.'.join(map(str, n))}")
        seen.add(n)
        if i and n < nums[i - 1]:
            problems.append(f"L6 section {'.'.join(map(str, n))} appears after "
                            f"{'.'.join(map(str, nums[i - 1]))}")

    # L8: verifier-reported verification class must agree with the claims table.
    allowed_by_rule = {}
    for row in rows:
        for rule in row_rules(row):
            allowed_by_rule.setdefault(rule, set()).update(row_classes(row))
    try:
        tree = ast.parse(verifier_src)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute) or node.func.attr != "check":
                continue
            # r.check(ok, label, cls, rule) -- only literal pairs are release-linted.
            if len(node.args) >= 4 and isinstance(node.args[2], ast.Constant) and isinstance(node.args[3], ast.Constant):
                cls, rule = node.args[2].value, node.args[3].value
                if isinstance(cls, str) and isinstance(rule, str) and rule in allowed_by_rule:
                    if cls not in allowed_by_rule[rule]:
                        problems.append(f"L8 {rule}: verifier emits class {cls}, claims table allows {sorted(allowed_by_rule[rule])}")
    except SyntaxError as exc:
        problems.append(f"L8 verifier cannot be parsed: {exc}")

    # counts
    cls_count, sup_count = {}, {}
    for row in rows:
        for c in row_classes(row):
            cls_count[c] = cls_count.get(c, 0) + 1
        sup_count[row_support(row)] = sup_count.get(row_support(row), 0) + 1
    order = ["S", "C", "X", "T", "A"]
    cls_str = ", ".join(f"**{k}** {cls_count.get(k, 0)}" for k in order)
    sup_str = ", ".join(f"**{k}** {sup_count.get(k, 0)}"
                        for k in ["implemented", "partial", "not_implemented", "not applicable", "out of scope"]
                        if sup_count.get(k))
    line_cls = f"Verification class: {cls_str}."
    line_sup = f"Reference verifier support: {sup_str}."

    if a.emit_counts:
        print(line_cls)
        print(line_sup)
        print(f"Rows: {len(rows)}")
        return 0

    # L7
    claims_src = open(CLAIMS).read()
    for expected in (line_cls, line_sup):
        if expected not in claims_src:
            problems.append(f"L7 CLAIMS-CLASSIFICATION counts are stale; recomputed: {expected}")
    m = re.search(r"Current counts:([^\n]*)", spec_src)
    if m:
        want = (f"Current counts: {cls_count.get('S', 0)} S, {cls_count.get('C', 0)} C, "
                f"{cls_count.get('X', 0)} X, {cls_count.get('T', 0)} T, {cls_count.get('A', 0)} A; "
                f"{sup_count.get('implemented', 0)} implemented, {sup_count.get('partial', 0)} partial, "
                f"{sup_count.get('not_implemented', 0)} not implemented.")
        if want not in spec_src:
            problems.append(f"L7 Annex D counts are stale; recomputed: {want}")

    version_line = re.search(r"\*\*Version:\*\*\s*([^\n]+)", spec_src)

    # L8: the review-provenance slot is a release gate, not a promise in prose.
    # The specification says attribution must be resolved before the permanent
    # release; this encodes that sentence so a candidate may circulate with the
    # slot open while a non-candidate build cannot.
    is_candidate = bool(version_line) and "rc" in version_line.group(1).lower()
    if "REVIEW-SYSTEM-UNSPECIFIED" in spec_src and not is_candidate:
        problems.append("L8 review provenance names no specific system, which a permanent "
                        "release may not do; resolve the disclosure or keep the version a candidate")

    # L0: a requirement identifier must denote exactly one requirement. Two rows
    # sharing an ID makes the ID useless as a cross-reference and silently
    # corrupts the machine-generated counts.
    seen_ids = {}
    for row in rows:
        seen_ids.setdefault(row["id"], []).append(row["requirement"][:60])
    for rid, reqs in seen_ids.items():
        if len(reqs) > 1:
            problems.append(f"L0 requirement id {rid} appears {len(reqs)} times: {reqs}")

    # L9: a candidate must not carry stale version strings outside its changelog.
    if version_line:
        current = version_line.group(1).split()[0].strip()
        head = spec_src.split("## Annex C: Changelog")[0]
        for stale in set(re.findall(r"0\.2\.0-rc\d+", head)):
            if stale != current:
                problems.append(f"L9 specification body carries stale version string {stale} "
                                f"while declaring {current}")
        for path in ("README.md", "run_all.sh"):
            fp = os.path.join(ROOT, path)
            if os.path.exists(fp):
                for stale in set(re.findall(r"0\.2\.0-rc\d+", open(fp).read())):
                    if stale != current:
                        problems.append(f"L9 {path} carries stale version string {stale}")

    # L10: the working-tree release manifest must describe the working tree.
    # The published archive regenerates it at build time, so a stale in-repo copy
    # verifies clean from the ZIP and fails for anyone verifying from the
    # repository. One artifact, two truths.
    man = os.path.join(ROOT, "RELEASE-MANIFEST.sha256")
    if os.path.exists(man):
        import hashlib
        stale = missing = 0
        listed = set()
        for line in open(man):
            parts = line.split(None, 1)
            if len(parts) != 2:
                continue
            want, rel = parts[0], parts[1].strip()
            listed.add(rel)
            fp = os.path.join(ROOT, rel)
            if not os.path.exists(fp):
                missing += 1
            elif hashlib.sha256(open(fp, "rb").read()).hexdigest() != want:
                stale += 1
        if stale or missing:
            problems.append(f"L10 working-tree RELEASE-MANIFEST.sha256 is stale: "
                            f"{stale} digest mismatches, {missing} listed files absent")

    if not a.quiet:
        print(f"release lint: {len(rows)} requirement rows, {len(verifier_rules)} verifier rules, "
              f"{len(asserted)} rule-asserting fixtures")
        print(f"  {line_cls}")
        print(f"  {line_sup}")
    check_changelog_counts(problems)
    for p in problems:
        print(f"  LINT FAIL {p}")
    print(f"release lint: {len(problems)} problems")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
