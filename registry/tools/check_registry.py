#!/usr/bin/env python3
"""Check the registry, and check that SCORECARD.md counts what it holds.

Two statements of one fact drift unless something compares them. The scorecard
states counts; the registry holds the evidence. This check derives each count
from the files and fails when the scorecard says anything else, so a count can
move only in the pull request that publishes its evidence.

Standard library only. `--self-test` exercises the rules on temporary trees.
"""
import datetime
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FORMAT = "dses-registry-transcript/1"
HEX64 = re.compile(r"^[0-9a-f]{64}$")
SLUG = re.compile(r"^[a-z0-9][a-z0-9-]*$")
REPORT = re.compile(r"^([a-z0-9][a-z0-9-]*)-(implementation|interoperability)-(\d{4}-\d{2}-\d{2})\.md$")
REVIEW = re.compile(r"^(statistics|protocol|health-law)-[a-z0-9-]+-[0-9a-z.-]+\.md$")

ENUMS = {
    ("status",): {"published", "withdrawn"},
    ("implementation", "kind"): {"emitter", "adapter", "verifier"},
    ("implementation", "independence"): {"independent", "reference-derived", "reference"},
    ("implementation", "reference_code_reused"): {"none", "partial", "full"},
    ("deployment", "status"): {"none", "planned", "live"},
    ("deployment", "emitter"): {"own", "reference"},
    ("evidence_package", "data_class"): {"synthetic", "deidentified", "locally-reproducible"},
}
SETTINGS = {"reader-study", "acceptance-test", "production-logging"}
REQUIRED_TEXT = [
    ("organization",), ("accountable_lead",), ("workflow",), ("evidence_question",),
    ("dses_version",), ("capture_level",), ("integrity_class",),
    ("implementation", "language"), ("implementation", "source_location"),
    ("implementation", "maintained_by"), ("implementation", "ai_assistance"),
    ("evidence_package", "location"), ("limitations",),
]
# Scorecard row label prefix -> derived count key.
ROWS = [
    ("Independent implementations", "independent_implementations"),
    ("Real deployments", "real_deployments"),
    ("Implementing organizations", "implementing_organizations"),
    ("Named external expert reviewers", "named_reviews"),
    ("Implementation or interoperability reports", "reports"),
    ("Interoperability reports", "reports"),
    ("Conformance transcripts", "conformance_transcripts"),
]


def get(d, path):
    for k in path:
        if not isinstance(d, dict) or k not in d:
            return None
        d = d[k]
    return d


def is_date(s):
    try:
        datetime.date.fromisoformat(s)
        return True
    except (TypeError, ValueError):
        return False


def listing(path, suffix):
    if not os.path.isdir(path):
        return []
    return sorted(n for n in os.listdir(path)
                  if n.endswith(suffix) and n != "README.md")


def check(root):
    """Return (errors, counts) for the tree at root."""
    errors = []
    reg = os.path.join(root, "registry")
    err = errors.append

    archives = {}
    ap = os.path.join(reg, "archives.json")
    if os.path.exists(ap):
        archives = {k: v for k, v in json.load(open(ap, encoding="utf8")).items()
                    if not k.startswith("_")}

    report_files = listing(os.path.join(reg, "reports"), ".md")
    transcript_files = listing(os.path.join(reg, "transcripts"), ".json")

    # --- implementation entries -------------------------------------------
    entries = {}
    impl_dir = os.path.join(reg, "implementations")
    for slug in sorted(os.listdir(impl_dir)) if os.path.isdir(impl_dir) else []:
        d = os.path.join(impl_dir, slug)
        if not os.path.isdir(d):
            continue
        where = f"implementations/{slug}/entry.json"
        p = os.path.join(d, "entry.json")
        if not os.path.exists(p):
            err(f"{where}: missing")
            continue
        try:
            e = json.load(open(p, encoding="utf8"))
        except ValueError as ex:
            err(f"{where}: not valid JSON ({ex})")
            continue
        if not SLUG.match(slug) or e.get("slug") != slug:
            err(f"{where}: slug must be lowercase and equal the directory name")
        for path, allowed in ENUMS.items():
            v = get(e, path)
            if v not in allowed:
                err(f"{where}: {'.'.join(path)} is {v!r}, expected one of {sorted(allowed)}")
        for path in REQUIRED_TEXT:
            v = get(e, path)
            if not isinstance(v, str) or not v.strip():
                err(f"{where}: {'.'.join(path)} is required")
        if not HEX64.match(str(get(e, ("evidence_package", "sha256")) or "")):
            err(f"{where}: evidence_package.sha256 must be 64 lowercase hex characters")
        indep = get(e, ("implementation", "independence"))
        if indep == "independent" and get(e, ("implementation", "reference_code_reused")) != "none":
            err(f"{where}: an independent implementation reuses no reference emitter code")
        dep = e.get("deployment") or {}
        if dep.get("status") in ("planned", "live") and dep.get("setting") not in SETTINGS:
            err(f"{where}: deployment.setting must be one of {sorted(SETTINGS)}")
        if dep.get("status") == "live":
            if not (is_date(dep.get("first_record_date")) and is_date(dep.get("last_record_date"))):
                err(f"{where}: a live deployment states first and last record dates (YYYY-MM-DD)")
            n = dep.get("record_count_aggregate")
            if not isinstance(n, int) or isinstance(n, bool) or n < 1:
                err(f"{where}: a live deployment states an aggregate record count of at least 1")
        if indep == "independent" and dep.get("emitter") == "reference":
            err(f"{where}: an independent implementation's deployment uses its own emitter")
        for name in e.get("reports") or []:
            if name not in report_files:
                err(f"{where}: lists report {name}, not found under reports/")
        for name in e.get("transcripts") or []:
            if name not in transcript_files:
                err(f"{where}: lists transcript {name}, not found under transcripts/")
        entries[slug] = e

    published = {s: e for s, e in entries.items() if e.get("status") == "published"}

    # --- reports ----------------------------------------------------------
    for name in report_files:
        m = REPORT.match(name)
        if not m:
            err(f"reports/{name}: name must be <slug>-implementation|interoperability-YYYY-MM-DD.md")
            continue
        if not is_date(m.group(3)):
            err(f"reports/{name}: date is not a real date")
        listed = [s for s, e in published.items() if name in (e.get("reports") or [])]
        if not listed:
            err(f"reports/{name}: no published entry lists this report")
        text = open(os.path.join(reg, "reports", name), encoding="utf8").read()
        if f"Kind: {m.group(2)} report" not in text:
            err(f"reports/{name}: body must carry the line 'Kind: {m.group(2)} report'")

    # --- transcripts ------------------------------------------------------
    for name in transcript_files:
        where = f"transcripts/{name}"
        try:
            t = json.load(open(os.path.join(reg, "transcripts", name), encoding="utf8"))
        except ValueError as ex:
            err(f"{where}: not valid JSON ({ex})")
            continue
        if t.get("transcript_format") != FORMAT:
            err(f"{where}: transcript_format must be {FORMAT}")
        slug = t.get("implementation")
        if slug not in published:
            err(f"{where}: implementation {slug!r} has no published entry")
        elif name not in (published[slug].get("transcripts") or []):
            err(f"{where}: its entry does not list this transcript")
        if t.get("exit_code") != 0:
            err(f"{where}: exit code {t.get('exit_code')!r}; a run with failures is evidence for an "
                f"implementation report, not a conformance transcript")
        out = t.get("output")
        if not isinstance(out, str) or not out.strip():
            err(f"{where}: verbatim command output is required")
        elif hashlib.sha256(out.encode("utf8")).hexdigest() != t.get("output_sha256"):
            err(f"{where}: output does not match output_sha256")
        if not t.get("command"):
            err(f"{where}: the command that was run is required")
        ver = t.get("dses_version")
        digest = get(t, ("specification_archive", "sha256"))
        if ver not in archives:
            err(f"{where}: dses_version {ver!r} is not in registry/archives.json")
        elif digest != archives[ver].get("sha256"):
            err(f"{where}: archive digest is not the published digest for {ver}")
        subs = t.get("subjects") or []
        if not subs or any(not HEX64.match(str(s.get("sha256") or "")) for s in subs):
            err(f"{where}: at least one subject with a SHA-256 is required")
        env = t.get("environment") or {}
        if not env.get("os") or not (env.get("packages") or env.get("extra")):
            err(f"{where}: environment record needs the OS and pinned dependency versions")
        for field in ("organization", "accountable_lead", "claim_scope"):
            if not str(t.get(field) or "").strip():
                err(f"{where}: {field} is required")

    # --- named reviews (published in docs/reviews, counted here) ----------
    reviews = [n for n in listing(os.path.join(root, "docs", "reviews"), ".md")
               if REVIEW.match(n)]

    counts = {
        "implementing_organizations": len({e["organization"].strip() for e in published.values()
                                           if get(e, ("implementation", "independence")) != "reference"
                                           and isinstance(e.get("organization"), str)}),
        "independent_implementations": sum(
            1 for e in published.values()
            if get(e, ("implementation", "independence")) == "independent"),
        "real_deployments": sum(
            1 for e in published.values() if get(e, ("deployment", "status")) == "live"),
        "reports": len(report_files),
        "conformance_transcripts": len(transcript_files),
        "named_reviews": len(reviews),
    }

    # --- scorecard agreement ---------------------------------------------
    sp = os.path.join(root, "SCORECARD.md")
    seen = set()
    for line in open(sp, encoding="utf8") if os.path.exists(sp) else []:
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3:
            continue
        for prefix, key in ROWS:
            if cells[0].startswith(prefix) and key not in seen:
                seen.add(key)
                m = re.match(r"(\d+)", cells[1])
                if not m:
                    err(f"SCORECARD.md: row '{cells[0]}' has no leading count")
                elif int(m.group(1)) != counts[key]:
                    err(f"SCORECARD.md: row '{cells[0]}' says {m.group(1)}, "
                        f"the registry holds {counts[key]}")
    for key in counts:
        if key not in seen:
            err(f"SCORECARD.md: no row found for {key.replace('_', ' ')}")
    return errors, counts


def report(root):
    errors, counts = check(root)
    for e in errors:
        print(f"REGISTRY  {e}")
    print("registry check: " + ", ".join(f"{v} {k.replace('_', ' ')}" for k, v in counts.items())
          + f"; {len(errors)} problem(s)")
    return 1 if errors else 0


# ---------------------------------------------------------------------------
def self_test():
    digest = "ab" * 32
    scorecard = lambda o, i, d, r, t, v: (
        "| Signal | Now | Target |\n|---|---|---|\n"
        f"| Independent implementations (non-reference) | {i} | 2 |\n"
        f"| Real deployments | {d} | 3 |\n| Implementing organizations | {o} | 5 |\n"
        f"| Named external expert reviewers | {v} human | 3 |\n"
        f"| Implementation or interoperability reports | {r} | 5 |\n"
        f"| Conformance transcripts in registry | {t} | 3 |\n")

    def entry(**over):
        e = {
            "slug": "acme", "status": "published", "organization": "Acme Health",
            "accountable_lead": "A. Person", "contact": "", "workflow": "w",
            "evidence_question": "q", "dses_version": "0.2.0", "capture_level": "L1",
            "integrity_class": "I1",
            "implementation": {"kind": "emitter", "language": "Go", "source_location": "x",
                               "independence": "independent", "reference_code_reused": "none",
                               "maintained_by": "Acme", "ai_assistance": "none"},
            "deployment": {"status": "none", "setting": "", "first_record_date": "",
                           "last_record_date": "", "record_count_aggregate": None, "emitter": "own"},
            "evidence_package": {"location": "x", "sha256": digest, "data_class": "synthetic"},
            "reports": ["acme-implementation-2027-01-15.md"],
            "transcripts": ["acme-0.2.0.json"], "limitations": "l",
        }
        for k, v in over.items():
            if isinstance(v, dict):
                e[k] = {**e[k], **v}
            else:
                e[k] = v
        return e

    def transcript(**over):
        out = "2205 checks, 0 failures\n"
        t = {"transcript_format": FORMAT, "implementation": "acme", "organization": "Acme Health",
             "accountable_lead": "A. Person", "dses_version": "0.2.0", "claim_scope": "s",
             "specification_archive": {"file": "a.zip", "sha256": digest},
             "subjects": [{"file": "p.json", "sha256": digest}], "command": ["verify"],
             "exit_code": 0, "output": out,
             "output_sha256": hashlib.sha256(out.encode()).hexdigest(),
             "environment": {"os": "Linux", "packages": {"jcs": "0.2.1"}, "extra": {}}}
        t.update(over)
        return t

    def build(tmp, sc, e=None, t=None, rep=True, review=None):
        reg = os.path.join(tmp, "registry")
        for d in ("implementations", "reports", "transcripts"):
            os.makedirs(os.path.join(reg, d))
        os.makedirs(os.path.join(tmp, "docs", "reviews"))
        json.dump({"0.2.0": {"sha256": digest}}, open(os.path.join(reg, "archives.json"), "w"))
        open(os.path.join(tmp, "SCORECARD.md"), "w").write(sc)
        if e is not None:
            os.makedirs(os.path.join(reg, "implementations", "acme"))
            json.dump(e, open(os.path.join(reg, "implementations", "acme", "entry.json"), "w"))
            if rep:
                open(os.path.join(reg, "reports", "acme-implementation-2027-01-15.md"), "w").write(
                    "- Kind: implementation report\n")
        if t is not None:
            json.dump(t, open(os.path.join(reg, "transcripts", "acme-0.2.0.json"), "w"))
        if review:
            open(os.path.join(tmp, "docs", "reviews", review), "w").write("x\n")

    live = {"status": "live", "setting": "reader-study", "first_record_date": "2027-01-10",
            "last_record_date": "2027-02-01", "record_count_aggregate": 40, "emitter": "own"}
    cases = [
        ("empty registry, zero scorecard", dict(sc=scorecard(0, 0, 0, 0, 0, 0)), None),
        ("full valid entry, scorecard agrees",
         dict(sc=scorecard(1, 1, 0, 1, 1, 0), e=entry(), t=transcript()), None),
        ("evidence published but scorecard not moved",
         dict(sc=scorecard(0, 0, 0, 0, 0, 0), e=entry(), t=transcript()), "the registry holds"),
        ("scorecard moved with no evidence", dict(sc=scorecard(1, 0, 0, 0, 0, 0)), "the registry holds"),
        ("transcript with a failing run",
         dict(sc=scorecard(1, 1, 0, 1, 1, 0), e=entry(), t=transcript(exit_code=1)), "exit code"),
        ("transcript against an unpublished archive digest",
         dict(sc=scorecard(1, 1, 0, 1, 1, 0), e=entry(),
              t=transcript(specification_archive={"file": "a", "sha256": "cd" * 32})),
         "not the published digest"),
        ("transcript output edited after the run",
         dict(sc=scorecard(1, 1, 0, 1, 1, 0), e=entry(), t=transcript(output="0 failures\n")),
         "does not match output_sha256"),
        ("transcript with no environment record",
         dict(sc=scorecard(1, 1, 0, 1, 1, 0), e=entry(), t=transcript(environment={})),
         "environment record"),
        ("independent claimed with reference code reused",
         dict(sc=scorecard(1, 1, 0, 1, 1, 0),
              e=entry(implementation={"reference_code_reused": "partial"}), t=transcript()),
         "reuses no reference emitter code"),
        ("reference-derived entry counts the organization, not independence",
         dict(sc=scorecard(1, 0, 0, 1, 1, 0),
              e=entry(implementation={"independence": "reference-derived",
                                      "reference_code_reused": "partial"}), t=transcript()), None),
        ("reference-emitter deployment counts as a deployment only",
         dict(sc=scorecard(0, 0, 1, 1, 0, 0),
              e=entry(implementation={"independence": "reference", "reference_code_reused": "full"},
                      deployment={**live, "emitter": "reference"}, transcripts=[])), None),
        ("live deployment with no record dates",
         dict(sc=scorecard(1, 1, 1, 1, 1, 0),
              e=entry(deployment={**live, "first_record_date": ""}), t=transcript()),
         "first and last record dates"),
        ("live deployment with zero records",
         dict(sc=scorecard(1, 1, 1, 1, 1, 0),
              e=entry(deployment={**live, "record_count_aggregate": 0}), t=transcript()),
         "aggregate record count"),
        ("live deployment, valid",
         dict(sc=scorecard(1, 1, 1, 1, 1, 0), e=entry(deployment=live), t=transcript()), None),
        ("withdrawn entry is not counted",
         dict(sc=scorecard(0, 0, 0, 0, 0, 0),
              e=entry(status="withdrawn", reports=[], transcripts=[]), rep=False), None),
        ("entry lists a report that is not there",
         dict(sc=scorecard(1, 1, 0, 0, 1, 0), e=entry(), t=transcript(), rep=False),
         "not found under reports/"),
        ("named review attestation is counted",
         dict(sc=scorecard(0, 0, 0, 0, 0, 1), review="statistics-baird-0.2.0.md"), None),
        ("attestation published but scorecard not moved",
         dict(sc=scorecard(0, 0, 0, 0, 0, 0), review="statistics-baird-0.2.0.md"),
         "the registry holds"),
        ("dispositions file is not an attestation",
         dict(sc=scorecard(0, 0, 0, 0, 0, 0), review="dispositions-0.2.0.md"), None),
    ]
    failed = 0
    for name, kw, expect in cases:
        tmp = tempfile.mkdtemp()
        try:
            build(tmp, **kw)
            errors, _ = check(tmp)
        finally:
            shutil.rmtree(tmp)
        ok = (not errors) if expect is None else any(expect in e for e in errors)
        if not ok:
            failed += 1
            print(f"FAIL  {name}: expected {expect or 'no errors'}, got {errors}")
    print(f"registry self-test: {len(cases) - failed} cases passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        sys.exit(self_test())
    sys.exit(report(ROOT))
