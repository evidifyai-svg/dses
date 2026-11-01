#!/usr/bin/env python3
"""Tests for scripts/check_rendered_claims.py.

The shipped claims file must pass with exactly the errata ERRATA-v0.2.md
records. Each kind of drift the check exists to catch must then fail with its
own code, on a copy of the package so nothing shipped is touched: a number
changed or added in the prose, a number changed in the artifact, an erratum
fixed in the prose without its claims moving, an erratum the errata file does
not record, an erratum that no longer disagrees, a correction whose own number
is wrong or unclaimed, and claims files that are malformed or that reach
outside the closed expression language.
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Callable, List, Optional

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import check_rendered_claims as crc  # noqa: E402

CLAIMS = ROOT / "tests" / "rendered_claims" / "RELIANCE-CONTEXT-EXAMPLE.claims.json"
SPEC = json.loads(CLAIMS.read_text(encoding="utf8"))
ERRATA = "ERRATA-v0.2.md"

failures: List[str] = []
passed = 0


def expect(name: str, ok: bool, detail: str = "") -> None:
    global passed
    if ok:
        passed += 1
    else:
        failures.append(f"{name}{': ' + detail if detail else ''}")


def run_copy(doc: Optional[Callable[[str], str]] = None,
             artifact: Optional[Callable[[dict], None]] = None,
             errata: Optional[Callable[[str], str]] = None,
             claims: Optional[Callable[[dict], None]] = None) -> crc.Report:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        for rel in [SPEC["document"], *SPEC["sources"].values(), ERRATA]:
            (base / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / rel, base / rel)
        if doc:
            p = base / SPEC["document"]
            p.write_text(doc(p.read_text(encoding="utf8")), encoding="utf8")
        if artifact:
            p = base / SPEC["sources"]["artifact"]
            obj = json.loads(p.read_text(encoding="utf8"))
            artifact(obj)
            p.write_text(json.dumps(obj), encoding="utf8")
        if errata:
            p = base / ERRATA
            p.write_text(errata(p.read_text(encoding="utf8")), encoding="utf8")
        spec = json.loads(json.dumps(SPEC))
        if claims:
            claims(spec)
        out = base / "tests" / "rendered_claims" / CLAIMS.name
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(spec), encoding="utf8")
        return crc.check_file(out, root=base)


def expect_codes(name: str, report: crc.Report, *codes: str) -> None:
    missing = [c for c in codes if c not in report.codes]
    expect(name, not missing and bool(report.failures),
           f"expected {list(codes)}, got {sorted(set(report.codes)) or 'a pass'}")


def replace_once(old: str, new: str) -> Callable[[str], str]:
    def f(text: str) -> str:
        if text.count(old) != 1:
            raise AssertionError(f"test fixture text not found exactly once: {old!r}")
        return text.replace(old, new)
    return f


# ---- shipped claims ---------------------------------------------------------

shipped = crc.check_file(CLAIMS)
c = shipped.counts
expect("shipped claims pass", not shipped.failures, "; ".join(m for _, m in shipped.failures[:5]))
expect("shipped claims carry exactly the two recorded errata", c["known_errata"] == 2, str(c))
expect("every number in the shipped example is accounted for",
       c["claims"] + c["not_counts"] + c["known_errata"] == c["numbers"] and c["numbers"] > 0, str(c))
expect("every number in both corrected texts is verified", c["corrections"] == 6, str(c))

# ---- tokens, values, rounding, expressions ----------------------------------

toks = [t for _, _, t in crc.scan_tokens(
    "v0.2 kappa-fleiss-v1 vendor-pe-cad-2.1 `10` 2026-03-01 2026-08-12T01:00:00Z often someone none\n"
    "```\nfenced 42\n```\n"
    "Twenty-five, seventy-nine per cent, 33%, 1.00 and 7.")]
expect("tokenizer finds numbers and skips identifiers, code, dates and words that contain number words",
       toks == ["Twenty-five", "seventy-nine", "33%", "1.00", "7"], str(toks))
expect("compound number words", crc.token_value("Twenty-five")[0] == 25 and crc.token_value("seventy-nine")[0] == 79)
for stated, computed, want in [("33%", 100 / 3, True), ("34%", 100 / 3, False), ("12%", 12.5, True),
                               ("13%", 12.5, True), ("1.00", 1.0, True), ("1.0", 1.04, True),
                               ("1.0", 1.06, False), ("3", 3.0, True), ("3", 3.2, False),
                               ("three", 3, True), ("three", 2.6, False)]:
    expect(f"matches({stated!r}, {computed:g}) is {want}", crc.matches(stated, computed) is want)
expect("rnd rounds halves up", crc.evaluate("rnd(2.5)", {}) == 3 and crc.evaluate("rnd(pct1(0.7923))", {}) == 79)
expect("days counts whole days elapsed",
       crc.evaluate("days('2026-03-01T00:00:00Z', '2026-06-30T23:59:59Z')", {}) == 121)
expect("key0 reads an absent count as zero", crc.evaluate("key0(x, 'absent')", {"x": {}}) == 0)
for bad in ["__import__('os').getcwd()", "x.__class__", "open('f')", "pct(1, 0)", "x.y", "[1][0]", "'a' + 'b'"]:
    try:
        crc.evaluate(bad, {"x": {}})
        expect(f"refuses {bad!r}", False, "evaluated")
    except crc.ClaimError as err:
        expect(f"refuses {bad!r}", err.code == "BAD_EXPR", err.code)

# ---- drift in the prose, the artifact and the errata ------------------------

expect_codes("a percentage changed in the prose",
             run_copy(doc=replace_once("1 of 3, or 33%", "1 of 3, or 34%")), "QUOTE_NOT_FOUND", "UNACCOUNTED")
expect_codes("a number added to the prose",
             run_copy(doc=lambda t: t + "\nThe panel met 4 times.\n"), "UNACCOUNTED")


def more_assigned(a: dict) -> None:
    a["reliance_context"]["subject_decision_instance_count"] = 11


def wider_interval(a: dict) -> None:
    a["interval"]["upper"] = 0.80


expect_codes("a count changed in the artifact", run_copy(artifact=more_assigned), "MISMATCH")
expect_codes("a percentage the prose no longer rounds correctly", run_copy(artifact=wider_interval), "MISMATCH")
expect_codes("an erratum fixed in the prose without its claims moving",
             run_copy(doc=replace_once("Twenty-five of the\nreader's other decision-opportunities",
                                       "Five of the\nreader's other metric-eligible instances")),
             "QUOTE_NOT_FOUND", "UNACCOUNTED")
expect_codes("an erratum the errata file does not record",
             run_copy(errata=replace_once("Twenty-five of the reader's other decision-opportunities",
                                          "Several of the reader's other decision-opportunities")),
             "UNRECORDED_ERRATUM")


def erratum_agrees(s: dict) -> None:
    s["knownErrata"][0]["expr"] = "25"


expect_codes("an erratum that no longer disagrees", run_copy(claims=erratum_agrees), "STALE_ERRATUM")


def wrong_correction(s: dict) -> None:
    e = s["knownErrata"][0]
    e["correctedQuote"] = e["correctedQuote"].replace("and seven of the ten", "and eight of the ten")
    for fix in e["corrected"]:
        if fix["number"] == "seven":
            fix["number"] = "eight"


expect_codes("a correction whose own number is wrong",
             run_copy(errata=replace_once("and seven of\nthe ten assigned", "and eight of\nthe ten assigned"),
                      claims=wrong_correction), "CORRECTION_MISMATCH")


def unclaimed_correction(s: dict) -> None:
    s["knownErrata"][0]["corrected"] = [f for f in s["knownErrata"][0]["corrected"] if f["number"] != "ten"]


expect_codes("a number in corrected text left unclaimed", run_copy(claims=unclaimed_correction),
             "CORRECTION_UNACCOUNTED")

# ---- malformed claims files -------------------------------------------------


def duplicate(s: dict) -> None:
    s["claims"].append(dict(s["claims"][0]))


def ambiguous(s: dict) -> None:
    s["claims"].append({"quote": "1 of 3", "number": "1", "expr": "artifact.numerator"})


def outside_language(s: dict) -> None:
    s["claims"][0]["expr"] = "__import__('os').getcwd()"


def absent_field(s: dict) -> None:
    s["claims"][0]["expr"] = "artifact.numerater"


def no_reason(s: dict) -> None:
    s["notCounts"][0]["reason"] = " "


def misspelled(s: dict) -> None:
    s["claims"][0]["occurence"] = 1


def wrong_number(s: dict) -> None:
    s["claims"][0]["number"] = "2"


def escaping(s: dict) -> None:
    s["sources"]["artifact"] = "../outside.json"


for name, mutate, code in [
    ("a number claimed twice", duplicate, "DOUBLE_COVERED"),
    ("a quote that occurs twice", ambiguous, "QUOTE_NOT_UNIQUE"),
    ("an expression outside the closed language", outside_language, "BAD_EXPR"),
    ("a field the artifact does not have", absent_field, "BAD_EXPR"),
    ("a not-a-count entry without a reason", no_reason, "BAD_ENTRY"),
    ("a misspelled key", misspelled, "BAD_ENTRY"),
    ("a number the quote does not contain", wrong_number, "NUMBER_NOT_IN_QUOTE"),
    ("a source path outside the package", escaping, "BAD_ENTRY"),
]:
    expect_codes(name, run_copy(claims=mutate), code)

for f in failures:
    print(f"FAIL   {f}")
print(f"rendered claims tests: {passed} cases passed, {len(failures)} failed")
sys.exit(1 if failures else 0)
