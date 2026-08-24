# DSES v0.2.0-rc11 release notes (working record, docs/, not in the archive)

Cut 2026-08-24. Coherence pass ahead of named external review. No normative
model change.

## What the new gate steps found in rc10

1. `schemas/dses-v0.2-definitions.schema.json` described anchor evidence as
   living in `artifact_anchored` events, the event the specification retired
   for `anchor_evidence_recorded`.
2. Section 3.8 and two docstrings named a flat `code_artifact_digest` field the
   schema replaced in rc4 with `code_artifact` plus an explicit locator.
3. `_walk_executables` in `dses_verify.py` still matched that flat field, so the
   generic sweep over definition-artifact executables had yielded nothing since
   rc4. Every binding depended on explicit use-site calls. Fixed; and each
   executable reference is now checked once, not at every use site. Checks
   2,286 to 2,205. The 81 were repeats.
4. Section 3.4 named anchoring grade labels (`declared`, `checkpoint_relative`,
   `externally_anchored`, `asserted_unverified`) the verifier never reports and
   one it never derives. Now claim 3.4f, partial.
5. ENVIRONMENTS.md carried 199/2027/113/68 against a gate producing
   206/2286/158/101, and recorded Environment B green on a host whose system
   interpreter lacks jcs (the venv has it; the gate was run outside the venv).

## Gate additions

- step 7 `scripts/check_vocabulary.py` + `scripts/vocabulary-allow.json`
- step 8 `scripts/check_environments.py` (writes and checks the counts block)
- step 9 `scripts/check-language.mjs --config scripts/guard-spec.json` over the
  release tree; site profile unchanged
- `scripts/bump_version.py` owns the label; lint L9 polices its file list and
  the shipped example

## Gate at this candidate

lint 0, 206 objects, 2205 checks, OL CONFORMANT, 158/158, quickstart 2 passed
6 rejected, vocabulary 833 terms 0 findings, language guard 109 files 0 errors
33 warnings (all bare-noun DSES).

Reproduced with identical counts in two environments: the authoring Linux
container on Python 3.12, and macOS arm64 on Python 3.14.6 in a virtual
environment with an independently resolved transitive set.

## Digest discipline

The release digest is minted once, from the commit that carries the Environment
B record for this candidate, and is reproduced from that pushed commit in a
clean environment before it is published anywhere. Digests built from a working
tree that matches no commit are discarded, not recorded.

## Open after rc11

- site deploy with the final digest in the transcript, then tag with
  --prerelease and notes stating identifiers remain unminted pending named
  review and that passing the bundled gate does not establish independent
  implementation
- named human review packet against rc11 (Baird stats; crypto; health law)
- guard mechanism-term rule: disabled for the release tree by ruling
  2026-08-24 because v0.1 published those terms on 2026-08-15 and the
  provisionals lapsed; still armed for site copy. Revisit if that changes.
