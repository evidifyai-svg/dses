# DSES v0.2.0-rc12 release notes (working record, docs/, not in the archive)

Cut 2026-09-07. Release-engineering and companion artifacts. No normative model
change.

## What the new lint rule found in rc11

Lint L9 policed `bump_version.VERSIONED`. `make_release.py` shipped a different
and larger set. Nothing asserted the two agreed, so a shipped file could carry a
candidate label that no tool rewrote and no check read.

New rule L12 walks the actual shipped set, 106 members at rc11, and requires any
file carrying a candidate label to sit on a managed list. It found three:

1. `requirements.txt` declared rc10.
2. `scripts/dses_derivation.py` declared rc3.
3. `scripts/bump_version.py`'s own usage example named a specific candidate, so
   it went stale by construction.

The first two shipped inside the published rc11 archive. That archive contains
three different version labels.

## The engine label was never an oversight

Bringing `scripts/dses_derivation.py` onto VERSIONED and editing its docstring
changed its bytes and failed seven derived artifacts on DRV-ENGINE with no
indication of the cause.

It is the only reference script whose sha256 is registered inside
`examples/example-package.json`, twice. `dses_core.py`, `generate_example.py`
and `make_release.py` are not. Its identity is its digest, so a bump cannot
rewrite it without regenerating the whole worked example, and its label is
pinned to the candidate in which the engine itself last changed.

The file is restored byte for byte and comes off VERSIONED. A `DIGEST_BOUND`
list records why, and L12 verifies the registered digest directly, so a future
edit fails as one named invariant rather than as seven opaque verifier failures.

## The mint was blocked by tooling

`bump_version.py` matched only `X.Y.Z-rcN` and fullmatched its argument, so
`bump_version.py 0.2.0` was refused. The tool that owns the version label could
not write the label this project exists to reach. It now accepts an optional
candidate suffix.

Minting remains gated on purpose. L8 refused a non-candidate build while the
specification says REVIEW-SYSTEM-UNSPECIFIED. A dry mint surfaced a second hole
beside it: the bump rewrites the label but not the prose next to it, so a minted
Version line read `0.2.0 (Release candidate for public comment)`. L8 now fails
on that too. A dry mint of this tree fails on three things, all of them real
work and none of them tooling.

## Companion artifacts

`TERMINOLOGY.md`, `CLAIM-LEDGER.md` and `ERRATA-v0.2.md` now ship in the
archive and are policed by `check_vocabulary.py`.

TERMINOLOGY fixes the prose terms no checker can reach. CLAIM-LEDGER governs
what a person says about the schema to someone else, in eleven entries pairing
allowed wording with the extrapolation that is not allowed. ERRATA-v0.2 carries
no errata, because 0.2.0 is unpublished, and fixes the process instead.

The language guard found five errors in that new prose on first run, every one
of them a prohibition written with the prohibited string inside it. Rewritten
rather than allowlisted, so the rules stay armed in the files that exist to
state them.

## Section 8.2

Each reliance metric acronym is expanded once at its point of introduction.
RAIR as reliance on AI rescue, which was already the repository's own wording.
SRF and EAR follow the specification's existing prose. RSR had no published
expansion and is written as retained self-reliance, the complement the identity
SRF = 1 - RSR requires. The statistics lane is asked to confirm it.

## Gate at this candidate

lint 0, 206 objects, 2205 checks, OL CONFORMANT, 158/158, quickstart 2 passed 6
rejected, vocabulary 833 terms 0 findings, language guard 112 files 0 errors 37
warnings.

Two counts moved from rc11 because the shipped set grew: release manifest 106 to
109 entries, guard 109 to 112 files with warnings 33 to 37. The four new
warnings are the known adjective-plus-noun false positive.

Reproduced with identical counts and an identical archive digest in two
environments: the authoring Linux container on Python 3.12, and macOS arm64 in a
virtual environment with an independently resolved transitive set.

## Digest

`7c08d88e40393a470dfb8cfb69d34392abb7253162d4103fe2dcee1a4c18d05d`, 110 members.
Built three times across two architectures, byte-identical each time.

## Open after rc12

- Named human review. Four packets out since 2026-09-01 across the crypto and
  health law lanes; statistics in motion separately. This remains the gate.
- Independent implementations: zero. The count is published and the mint may
  proceed while recording it.
- `make_release.py` would build an archive at an output path naming one
  candidate from a tree labeled another, silently. It did exactly that during
  this cut, producing a file named for rc12 from an rc11 tree, one command away
  from publication under a version it did not contain. An assertion closing it
  landed on main after the rc12 tag, so it will first ship in rc13. The tagged
  rc12 archive is unaffected and its digest stands.

Note for anyone building from main after this point: main carries the
`make_release.py` assertion and the rc12 tag does not, so a build from main
produces a different archive digest than the published rc12 archive. That is
expected. Reviewers are pinned to the tag for exactly this reason.
