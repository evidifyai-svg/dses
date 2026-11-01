#!/usr/bin/env python3
"""Every count stated in a rendered example ties to the artifact it renders.

The reference verifier recomputes every figure inside an artifact. It does not
read the prose written around an artifact, and that prose is the part a review
body reads. v0.2.0 shipped a rendered example whose prose stated one count the
artifact does not contain (ERRATA-v0.2.md, Erratum 1) and put another in the
wrong category (Erratum 2). This check makes that kind of drift a gate failure.

Each rendered document has a claims file in tests/rendered_claims/. The check:

  1. finds every number in the document: digits, with an optional decimal part
     or percent sign, and cardinal number words such as "three" or
     "seventy-nine". Code spans, fenced blocks, ISO dates and numbers fused to
     an identifier (v0.2, kappa-fleiss-v1) are not numbers in this sense;
  2. requires every number to be accounted for exactly once: by a claim (a
     quoted passage, the number in it, and an expression over the source
     artifacts that must equal it), by a not-a-count entry that gives its
     reason, or by a known erratum;
  3. evaluates each claim against the artifacts the claims file names;
  4. requires each known erratum to still disagree with the artifact, to be
     recorded in the errata file it names, and to carry corrected text whose
     own numbers are all claimed and all agree with the artifact.

Comparison. A count must equal its expression exactly. A percentage or a
decimal must be a correct rounding of its expression at the precision written:
33% passes for 33.3 and 34% fails; at an exact tie either neighbor passes. A
figure written in words that is itself rounded uses rnd() in its expression,
so the rounding is visible in the claims file rather than assumed by the check.

Expressions are a closed language: a source name followed by dotted fields,
integer and decimal constants, + - * /, unary minus, and these functions:

  pct(n, d)      100 * n / d
  pct1(x)        100 * x, a proportion written as a percentage
  rnd(x)         x rounded to a whole number, halves up
  days(a, b)     whole days elapsed from instant a to instant b
  key(o, name)   field name of o, for names that are not identifiers
  key0(o, name)  as key, but an absent field reads as 0; the only way to
                 read an absence as zero, so that choice is visible

A field that is absent fails. A number nobody accounted for fails. A claim
that disagrees with its artifact fails. An erratum that no longer disagrees
fails, because the errata file then describes text that is no longer wrong.

Usage: python3 scripts/check_rendered_claims.py [CLAIMS.json ...]
Default: every tests/rendered_claims/*.claims.json.
"""
from __future__ import annotations

import ast
import json
import math
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent
CLAIMS_DIR = ROOT / "tests" / "rendered_claims"
SCHEMA = "dses-rendered-claims/1"

UNITS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
    "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
    "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18,
    "nineteen": 19,
}
TENS = {"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70,
        "eighty": 80, "ninety": 90}
_WORDS = "|".join(sorted(list(UNITS) + list(TENS) + ["hundred"], key=len, reverse=True))
TOKEN_RE = re.compile(
    r"(?<![\w.\-/])(?:\d+(?:\.\d+)?%?|(?:" + _WORDS + r")(?:-(?:" + _WORDS + r"))?)(?![\w]|\.\d|-\d)",
    re.IGNORECASE,
)
FENCE_RE = re.compile(r"^```.*?^```[^\n]*$", re.M | re.S)
CODE_RE = re.compile(r"`[^`\n]*`")
DATE_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}(?:T[0-9:.]+Z?)?\b")

TOP_KEYS = ({"schema", "document", "sources"}, {"claims", "notCounts", "knownErrata", "note"})
ENTRY_KEYS = {
    "claims": ({"quote", "number", "expr"}, {"occurrence", "note"}),
    "notCounts": ({"quote", "number", "reason"}, {"occurrence"}),
    "knownErrata": ({"quote", "number", "expr", "erratumFile", "erratumQuote", "correctedQuote", "corrected"},
                    {"occurrence", "note"}),
    "corrected": ({"number", "expr"}, {"occurrence", "note"}),
}
TEXT_FIELDS = {"quote", "number", "expr", "reason", "erratumFile", "erratumQuote", "correctedQuote"}


class ClaimError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


# ---------------------------------------------------------------- numbers ----

def scan_tokens(text: str) -> List[Tuple[int, int, str]]:
    """(start, end, text) for every number in the prose, in document order."""
    def blank(m: "re.Match[str]") -> str:
        return re.sub(r"[^\n]", " ", m.group())
    masked = FENCE_RE.sub(blank, text)
    masked = CODE_RE.sub(blank, masked)
    masked = DATE_RE.sub(blank, masked)
    return [(m.start(), m.end(), m.group()) for m in TOKEN_RE.finditer(masked)]


def token_value(text: str) -> Tuple[float, int, bool]:
    """(value, decimal places, is_count). A count is a whole number, in digits or words, without a percent sign."""
    t = text.lower()
    pct = t.endswith("%")
    core = t[:-1] if pct else t
    if re.fullmatch(r"\d+(?:\.\d+)?", core):
        places = len(core.split(".")[1]) if "." in core else 0
        return float(core), places, (not pct and places == 0)
    total = 0
    for part in core.split("-"):
        if part in UNITS:
            total += UNITS[part]
        elif part in TENS:
            total += TENS[part]
        elif part == "hundred":
            total = (total or 1) * 100
        else:
            raise ClaimError("BAD_NUMBER", f"unreadable number word {text!r}")
    return float(total), 0, not pct


def matches(stated: str, computed: float) -> bool:
    value, places, is_count = token_value(stated)
    if is_count:
        return computed == value
    return abs(computed - value) <= 0.5 * 10 ** -places + 1e-9


class Text:
    """A document with its numbers and a whitespace-insensitive index for quotes."""

    def __init__(self, label: str, raw: str):
        self.label = label
        self.raw = raw
        self.tokens = scan_tokens(raw)
        out: List[str] = []
        self.back: List[int] = []
        prev_space = False
        for i, ch in enumerate(raw):
            if ch.isspace():
                if prev_space:
                    continue
                out.append(" ")
                prev_space = True
            else:
                out.append(ch)
                prev_space = False
            self.back.append(i)
        self.norm = "".join(out)

    def contains(self, quote: str) -> bool:
        return re.sub(r"\s+", " ", quote).strip() in self.norm

    def span(self, quote: str) -> Tuple[int, int]:
        q = re.sub(r"\s+", " ", quote).strip()
        hits, at = [], self.norm.find(q)
        while at != -1:
            hits.append(at)
            at = self.norm.find(q, at + 1)
        if not hits:
            raise ClaimError("QUOTE_NOT_FOUND", f"{self.label}: quote not found: {quote!r}")
        if len(hits) > 1:
            raise ClaimError("QUOTE_NOT_UNIQUE", f"{self.label}: quote occurs {len(hits)} times, lengthen it: {quote!r}")
        return self.back[hits[0]], self.back[hits[0] + len(q) - 1] + 1

    def inside(self, span: Tuple[int, int]) -> List[int]:
        return [i for i, (s, e, _) in enumerate(self.tokens) if s >= span[0] and e <= span[1]]

    def locate(self, span: Tuple[int, int], quote: str, number: str, occurrence: Any) -> int:
        hits = [i for i in self.inside(span) if self.tokens[i][2].lower() == str(number).lower()]
        if not hits:
            raise ClaimError("NUMBER_NOT_IN_QUOTE", f"{self.label}: {number!r} is not a number inside {quote!r}")
        if occurrence is None:
            if len(hits) > 1:
                raise ClaimError("NUMBER_NOT_IN_QUOTE",
                                 f"{self.label}: {number!r} occurs {len(hits)} times in {quote!r}; give an occurrence")
            return hits[0]
        if isinstance(occurrence, bool) or not isinstance(occurrence, int) or not 1 <= occurrence <= len(hits):
            raise ClaimError("NUMBER_NOT_IN_QUOTE", f"{self.label}: occurrence {occurrence!r} of {number!r} in {quote!r}")
        return hits[occurrence - 1]

    def where(self, idx: int) -> str:
        start, _, text = self.tokens[idx]
        line = self.raw.count("\n", 0, start) + 1
        context = re.sub(r"\s+", " ", self.raw[max(0, start - 40):start + len(text) + 30])
        return f"{self.label}:{line}: ...{context}..."


# ------------------------------------------------------------ expressions ----

def _parse_time(v: Any) -> datetime:
    return datetime.fromisoformat(str(v).replace("Z", "+00:00"))


def _key(obj: Any, name: Any) -> Any:
    if not isinstance(obj, dict) or name not in obj:
        raise ClaimError("BAD_EXPR", f"field {name!r} is absent")
    return obj[name]


FUNCS = {
    "pct": lambda n, d: 100.0 * n / d,
    "pct1": lambda x: 100.0 * x,
    "rnd": lambda x: float(math.floor(x + 0.5)),
    "days": lambda a, b: float((_parse_time(b) - _parse_time(a)).days),
    "key": _key,
    "key0": lambda obj, name: (obj.get(name, 0) if isinstance(obj, dict) else _key(obj, name)),
}


def evaluate(expr: str, sources: Dict[str, Any]) -> float:
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as err:
        raise ClaimError("BAD_EXPR", f"unparseable expression {expr!r}: {err.msg}") from None

    def number(v: Any) -> bool:
        return isinstance(v, (int, float)) and not isinstance(v, bool)

    def ev(node: ast.AST) -> Any:
        if isinstance(node, ast.Expression):
            return ev(node.body)
        if isinstance(node, ast.Constant) and (number(node.value) or isinstance(node.value, str)):
            return node.value
        if isinstance(node, ast.Name):
            if node.id not in sources:
                raise ClaimError("BAD_EXPR", f"unknown source {node.id!r} in {expr!r}")
            return sources[node.id]
        if isinstance(node, ast.Attribute):
            return _key(ev(node.value), node.attr)
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
            a, b = ev(node.left), ev(node.right)
            if not (number(a) and number(b)):
                raise ClaimError("BAD_EXPR", f"arithmetic on a non-number in {expr!r}")
            if isinstance(node.op, ast.Add):
                return a + b
            if isinstance(node.op, ast.Sub):
                return a - b
            if isinstance(node.op, ast.Mult):
                return a * b
            if b == 0:
                raise ClaimError("BAD_EXPR", f"division by zero in {expr!r}")
            return a / b
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            v = ev(node.operand)
            if not number(v):
                raise ClaimError("BAD_EXPR", f"negation of a non-number in {expr!r}")
            return -v
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in FUNCS and not node.keywords:
            args = [ev(a) for a in node.args]
            try:
                return FUNCS[node.func.id](*args)
            except ClaimError:
                raise
            except (TypeError, ValueError, ZeroDivisionError) as err:
                raise ClaimError("BAD_EXPR", f"{node.func.id}() failed in {expr!r}: {err}") from None
        raise ClaimError("BAD_EXPR", f"expression form not allowed in {expr!r}: {type(node).__name__}")

    value = ev(tree)
    if not number(value):
        raise ClaimError("BAD_EXPR", f"expression {expr!r} is not a number")
    return float(value)


# ------------------------------------------------------------------ check ----

class Report:
    def __init__(self, label: str):
        self.label = label
        self.failures: List[Tuple[str, str]] = []
        self.known: List[str] = []
        self.counts = {"numbers": 0, "claims": 0, "not_counts": 0, "known_errata": 0, "corrections": 0}

    def fail(self, code: str, message: str) -> None:
        self.failures.append((code, message))

    @property
    def codes(self) -> List[str]:
        return [c for c, _ in self.failures]


def _shape(report: Report, section: str, entry: Any, where: str) -> bool:
    required, optional = ENTRY_KEYS[section]
    if not isinstance(entry, dict):
        report.fail("BAD_ENTRY", f"{where}: {section} entry is not an object")
        return False
    missing = required - set(entry)
    unknown = set(entry) - required - optional
    if missing or unknown:
        report.fail("BAD_ENTRY", f"{where}: {section} entry {entry.get('quote', entry.get('number'))!r}: "
                                 f"missing {sorted(missing)}, unknown {sorted(unknown)}")
        return False
    for k in sorted(required & TEXT_FIELDS):
        if not isinstance(entry[k], str) or not entry[k].strip():
            report.fail("BAD_ENTRY", f"{where}: {section} entry field {k!r} is empty")
            return False
    return True


def _inside_root(root: Path, rel: str) -> Path:
    base = root.resolve()
    p = (root / rel).resolve()
    if base not in p.parents:
        raise ClaimError("BAD_ENTRY", f"path {rel!r} leaves the package")
    return p


def check_file(path: Path, root: Path = ROOT) -> Report:
    report = Report(Path(path).name)
    try:
        spec = json.loads(Path(path).read_text(encoding="utf8"))
    except (OSError, ValueError) as err:
        report.fail("BAD_ENTRY", f"{report.label}: unreadable claims file: {err}")
        return report
    required, optional = TOP_KEYS
    if not isinstance(spec, dict) or required - set(spec) or set(spec) - required - optional:
        report.fail("BAD_ENTRY", f"{report.label}: top level must have {sorted(required)}, "
                                 f"and may have only {sorted(optional)} besides")
        return report
    if spec["schema"] != SCHEMA:
        report.fail("BAD_ENTRY", f"{report.label}: schema must be {SCHEMA}")
        return report
    try:
        doc = Text(spec["document"], _inside_root(root, spec["document"]).read_text(encoding="utf8"))
        sources = {name: json.loads(_inside_root(root, rel).read_text(encoding="utf8"))
                   for name, rel in spec["sources"].items()}
    except ClaimError as err:
        report.fail(err.code, f"{report.label}: {err}")
        return report
    except (OSError, ValueError, AttributeError) as err:
        report.fail("BAD_ENTRY", f"{report.label}: unreadable document or source: {err}")
        return report
    report.label = doc.label
    report.counts["numbers"] = len(doc.tokens)
    covered: Dict[int, str] = {}
    errata_texts: Dict[str, Text] = {}

    def cover(entry: Dict[str, Any], kind: str) -> Optional[int]:
        try:
            idx = doc.locate(doc.span(entry["quote"]), entry["quote"], entry["number"], entry.get("occurrence"))
        except ClaimError as err:
            report.fail(err.code, f"{kind}: {err}")
            return None
        if idx in covered:
            report.fail("DOUBLE_COVERED", f"{doc.label}: {entry['number']!r} in {entry['quote']!r} is accounted "
                                          f"for twice ({covered[idx]} and {kind})")
            return None
        covered[idx] = kind
        return idx

    def compute(expr: str, what: str) -> Optional[float]:
        try:
            return evaluate(expr, sources)
        except ClaimError as err:
            report.fail(err.code, f"{doc.label}: {what}: {err}")
            return None

    for entry in spec.get("claims", []):
        if not _shape(report, "claims", entry, doc.label):
            continue
        idx = cover(entry, "claim")
        if idx is None:
            continue
        computed = compute(entry["expr"], f"claim {entry['number']!r} in {entry['quote']!r}")
        if computed is None:
            continue
        report.counts["claims"] += 1
        if not matches(doc.tokens[idx][2], computed):
            report.fail("MISMATCH", f"{doc.label}: the text says {doc.tokens[idx][2]!r} in {entry['quote']!r}, "
                                    f"but {entry['expr']} = {computed:g}")

    for entry in spec.get("notCounts", []):
        if _shape(report, "notCounts", entry, doc.label) and cover(entry, "not a count") is not None:
            report.counts["not_counts"] += 1

    for entry in spec.get("knownErrata", []):
        if not _shape(report, "knownErrata", entry, doc.label):
            continue
        idx = cover(entry, "known erratum")
        if idx is None:
            continue
        stated = doc.tokens[idx][2]
        computed = compute(entry["expr"], f"erratum {stated!r}")
        if computed is None:
            continue
        if matches(stated, computed):
            report.fail("STALE_ERRATUM", f"{doc.label}: known erratum {stated!r} in {entry['quote']!r} now agrees "
                                         f"with {entry['expr']}; the errata file describes text that is no longer wrong")
            continue
        name = entry["erratumFile"]
        try:
            if name not in errata_texts:
                errata_texts[name] = Text(name, _inside_root(root, name).read_text(encoding="utf8"))
        except ClaimError as err:
            report.fail(err.code, f"{doc.label}: {err}")
            continue
        except OSError as err:
            report.fail("UNRECORDED_ERRATUM", f"{doc.label}: errata file unreadable: {err}")
            continue
        errata = errata_texts[name]
        if not errata.contains(entry["erratumQuote"]):
            report.fail("UNRECORDED_ERRATUM", f"{doc.label}: known erratum {stated!r} is not recorded in {name} "
                                              f"(looked for {entry['erratumQuote']!r})")
            continue
        try:
            corrected_span = errata.span(entry["correctedQuote"])
        except ClaimError as err:
            report.fail(err.code, f"corrected text: {err}")
            continue
        if not isinstance(entry["corrected"], list):
            report.fail("BAD_ENTRY", f"{doc.label}: erratum {stated!r}: corrected must be a list")
            continue
        claimed: Dict[int, bool] = {}
        ok = True
        for fix in entry["corrected"]:
            if not _shape(report, "corrected", fix, name):
                ok = False
                continue
            try:
                cidx = errata.locate(corrected_span, entry["correctedQuote"], fix["number"], fix.get("occurrence"))
            except ClaimError as err:
                report.fail(err.code, f"corrected text: {err}")
                ok = False
                continue
            if cidx in claimed:
                report.fail("DOUBLE_COVERED", f"{name}: {fix['number']!r} in the corrected text is claimed twice")
                ok = False
                continue
            claimed[cidx] = True
            value = compute(fix["expr"], f"correction {fix['number']!r} for erratum {stated!r}")
            if value is None:
                ok = False
                continue
            if not matches(errata.tokens[cidx][2], value):
                report.fail("CORRECTION_MISMATCH", f"{name}: the corrected text for {stated!r} says "
                                                   f"{errata.tokens[cidx][2]!r}, but {fix['expr']} = {value:g}")
                ok = False
        for cidx in errata.inside(corrected_span):
            if cidx not in claimed:
                report.fail("CORRECTION_UNACCOUNTED", f"number in corrected text is not claimed: {errata.where(cidx)}")
                ok = False
        if ok:
            report.counts["known_errata"] += 1
            report.counts["corrections"] += len(claimed)
            report.known.append(f"{doc.label}: {stated!r} in {entry['quote']!r} disagrees with {entry['expr']} = "
                                f"{computed:g}; recorded in {name}, whose corrected text agrees with the artifact "
                                f"({len(claimed)} numbers)")

    for i in range(len(doc.tokens)):
        if i not in covered:
            report.fail("UNACCOUNTED", f"number {doc.tokens[i][2]!r} is not accounted for: {doc.where(i)}")
    return report


def main(argv: List[str]) -> int:
    paths = [Path(a) for a in argv] or sorted(CLAIMS_DIR.glob("*.claims.json"))
    if not paths:
        print("rendered claims: no claims files found", file=sys.stderr)
        return 1
    failed = 0
    for p in paths:
        r = check_file(p)
        for note in r.known:
            print(f"KNOWN  {note}")
        for code, message in r.failures:
            print(f"FAIL   [{code}] {message}")
        c = r.counts
        print(f"rendered claims: {r.label}: {c['numbers']} numbers; {c['claims']} claims verified, "
              f"{c['not_counts']} not counts, {c['known_errata']} known errata with "
              f"{c['corrections']} corrected numbers verified; {len(r.failures)} failure(s)")
        failed += len(r.failures)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
