# DSES v0.2.0 release notes (working record, docs/, not in the archive)

Prepared 2026-10-18. The permanent release of the outcome-evidence layer,
minted from candidate rc14. No normative change from rc14. No mechanism, rule,
or schema structure change from rc10.

## What 0.2.0 is

- Schema `$id`s are `https://evidify.ai/schemas/dses/0.2.0/...` and are
  permanent under `GOVERNANCE.md`. Candidates rc1 through rc14 carried
  `/0.2.0-rcN/` identifiers and those stay at their tags.
- The text is rc14's text, with the label moved by `scripts/bump_version.py`,
  the five candidate-status sentences rewritten (Version line, 8.4, Annex D,
  citation, provenance), and a new Annex C entry for 0.2.0 that collapses
  rc10 through rc14.
- The worked example is regenerated once for the new label. Keys and hashes
  differ from rc14's; structure and verdicts do not.

## The review record, stated as it is

Named human expert review was requested in three lanes before the mint and
none completed. As of 2026-10-18:

- Protocol and cryptography: two reviewers were asked and did not reply or
  declined; a third was asked on October 11, 2026 and had not yet responded.
- Health law and clinical governance: two reviewers were asked and did not
  reply or declined; a third was asked on October 11, 2026 and had not yet
  responded.
- Statistics: a named biostatistician's review was in progress in person,
  with no written attestation.

Zero attestations in `docs/reviews/`. Zero independent implementations
(claim 7.3c). The author's ruling was to mint with the zero and record it.
The provenance section of `DSES-v0.2.md` carries the same record. Reviewer
identities are not recorded in this repository until an attestation is
published under the reviewer's name.

Standing policy for anything that arrives later: an attestation is published
verbatim in `docs/reviews/` under the reviewer's name with the version and
digest reviewed; objections get written dispositions the reviewer sees first;
a disposition that changes published text goes through `ERRATA-v0.2.md` or
into 0.2.1. Published text is never altered.

## How lint L8 was satisfied

L8 refuses a non-candidate build while `REVIEW-SYSTEM-UNSPECIFIED` stands in
the provenance section, and refuses a Version line that still calls itself a
candidate. Neither check was changed. The marker was removed by rewriting the
provenance paragraph to say what is actually known: the systems that built
the reference implementation and cut rc11 through 0.2.0 are named by vendor
and product; the per-round system behind the eleven review rounds was not
recorded at the time and the paragraph says so rather than reconstructing
it; and the human-review record is stated lane by lane with the mint date.

## Counts

Unchanged from rc14: 206 objects, 2205 checks, OL CONFORMANT, 158
rule-asserting cases rejected at the asserted rule, 1 boundary fixture held,
quickstart 2 valid examples and 6 targeted mutations, vocabulary 833 terms
and 0 findings, language guard 112 files 0 errors 37 warnings, release
manifest 109 entries, archive 110 members.

## Gate

ALL GREEN in Environment D (Linux x86_64, Python 3.13.16, fresh venv, pinned
requirements, Node 22) on the mint tree, on a fresh clone of the pushed
branch in a second fresh venv, and on the unpacked archive in a new empty
directory with zero extra files. Archive sha256 is recorded in the pull
request, the tag message and the GitHub release, and goes into the Zenodo
record's description by hand (see below). It is not recorded inside the
archive.

## What is still not established

An independently written implementation. Every environment above runs the
same reference code. See claim 7.3c and `SCORECARD.md`.

## Not in 0.2.0

No normative change. No reviewer disposition, because no objection was
received. No change to any lint rule, guard, or allowlist.

## Post-release record (2026-10-18)

- Tag `v0.2.0` (annotated) on `baaef23`, the squash-merge of #13. GitHub
  release `v0.2.0` published 22:16 UTC as Latest, not a prerelease. The
  release asset `dses-v0.2.0-publication.zip` was downloaded back from the
  release and re-hashed: sha256
  `a4a9b7f1beb0434bf55a48a581447c53d904e0930e59aac53a0c79c25b3375a1`,
  matching the gate.
- Environment B reproduced the archive before the tag was created: macOS
  26.6.2 (arm64), Python 3.14.6, cryptography 50.0.2, jsonschema 4.26.0,
  jsonschema-specifications 2025.9.1, jcs 0.2.1. The gate ran ALL GREEN, and
  the tag command ran only after the locally built archive hashed to the same
  sha256. `ENVIRONMENTS.md` ships inside the archive, so it keeps its 0.2.0
  text; Environment B moves into it at the next version.
- Zenodo: the GitHub integration created version 10.5281/zenodo.23460192
  under concept 10.5281/zenodo.21960297. The file it deposited is GitHub's
  source snapshot of tag `v0.2.0`, not the gate-built archive. The gate-built
  archive is the release asset above, and it rebuilds from that snapshot.
  Zenodo shows the publication date in Geneva time, 2026-10-19, until it is
  edited.
- dses.ai was deployed from main after the release and shows the archive
  digest and "minted October 18, 2026".
