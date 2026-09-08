# DSES: Decision-Sequence Evidence Schema

An open, vendor-neutral evidence vocabulary for reconstructing how human and
AI decision states were ordered.

## Start here

If you are adding DSES to an existing study, product, or validation workflow,
start with [`IMPLEMENT.md`](IMPLEMENT.md). It routes you to the smallest honest
capture pattern, two copy-paste synthetic flows, tiny Python and TypeScript
helpers, and the verification commands.

| Need | First implementation | Example |
|---|---|---|
| Record whether and how AI reached a person | Passive exposure logging at L1/I1 | [`quickstart/passive-exposure.json`](quickstart/passive-exposure.json) |
| Preserve pre-AI, reveal, and post-AI states with internally consistent ordering | Decision trajectory at L2/I2 | [`quickstart/sealed-sequence.json`](quickstart/sealed-sequence.json) |
| Bind outcomes and adjudication to a sequence | Outcome layer release candidate | [`DSES-v0.2.md`](DSES-v0.2.md) |

After installing the pinned dependencies, verify both quickstart flows with:

```sh
bash quickstart/verify.sh
```

Passing that command verifies the quickstart profile. It does **not** create a
`DSES Conformant` claim. See [`CONFORMANCE-POLICY.md`](CONFORMANCE-POLICY.md)
before publishing compatibility or conformance language.

## Version status

- **v0.1.2** is the latest tagged and archived release. Its normative sequence
  vocabulary remains in [`DSES-v0.1.md`](DSES-v0.1.md) and
  [`dses-v0.1.schema.json`](dses-v0.1.schema.json).
- **v0.2.0-rc12** is the current release candidate for the outcome-evidence
  layer. Its permanent `0.2.0` schema identifiers are intentionally unminted
  pending public comment and named human expert review.
- A release candidate is not a permanent release. Implementation reports may
  target it, but must name `0.2.0-rc12` exactly and expect change before 0.2.0.

This repository and `dses.ai` use `0.2.0-rc12` for the current candidate. The
older v0.1 tags remain immutable rather than being relabeled.

## Implement with the boundaries intact

- Use pseudonymous case and actor references. Keep raw, actor-resolved sequences
  local by default and export derived or aggregate evidence when possible.
- Sequence records do not determine causation, negligence, competence,
  liability, or a standard of care.
- Do not repurpose actor-resolved data for performance management absent prior
  documented governance, notice, access, case review, and appeal safeguards.
- Do not claim enforced ordering or external anchoring unless the deployed
  mechanism and external trust evidence establish those properties.

Use the [`IMPLEMENTATION-CHECKLIST.md`](IMPLEMENTATION-CHECKLIST.md) before a
pilot. Organizations willing to publish an implementation report can join the
[`Founding Implementer program`](FOUNDING-IMPLEMENTERS.md); its counts remain at
zero until the stated evidence is public.

## Reproduce every claim in the v0.2 candidate

```sh
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
bash run_all.sh
```

Build the clean publication archive with `python3 scripts/make_release.py`. The
builder uses an explicit allowlist, excludes caches, review notes, and nested
archives, fixes member ordering and timestamps, and adds
`RELEASE-MANIFEST.sha256` for the exact published bytes.

That runs seven stages, in this order for a reason:

0. `scripts/check_jcs.py` fails fast on canonicalization vectors chosen to catch
   common non-RFC-8785 JSON number spellings.
1. `scripts/release_lint.py` checks the publication contract: implemented
   verifier rules exist and have rule-asserting fixtures, verifier rule/class
   labels agree with the claims table, every uppercase conformance keyword in
   the specification carries an explicit requirement tag, section numbering is
   coherent, and generated claim counts are current.
2. `scripts/validate_package.py` validates the shipped v0.2 package envelope,
   cohort/case events, definition artifacts, and derived artifacts against four
   Draft 2020-12 schemas. The bundled decision sequences receive structural
   checks here and full hash-chain/payload-commitment replay in the verifier;
   they are not misdescribed as v0.2-schema-validated objects.
3. `scripts/dses_verify.py` is the outcome-layer reference verifier, run against
   the shipped artifacts with the worked example's trust store supplied
   explicitly. It recomputes hashes, replays chains, verifies payload
   commitments, verifies RFC 9162 proofs and signatures, runs declared rule
   modules against their fixtures, and recomputes metrics and disclosures from
   snapshot-frozen evidence.
4. `tests/run_regression.py` runs the adversarial suite. Every verifier fixture
   asserts the specific rule that must fire; cascading failures are allowed, so
   the suite does not claim that each mutation has only one rejection path.
5. `tests/run_quickstart.py` verifies the two external-implementation examples
   and rejects targeted mutations without representing that result as
   conformance.
6. Only then is the example regenerated into an isolated temporary copy,
   excluding local environments, VCS state, caches, and archives. This is a
   semantic regeneration check, not a claim of bit-for-bit archive reproduction.

## Trust anchors and witnesses

External anchor trust is never implicit. For the worked outcome-layer example,
run `scripts/dses_verify.py --anchor-trust examples/anchor-trust-store.json`; a
deployment verifier should supply its own trust policy and store.
`--witness witness.json` can additionally compare a separately held checkpoint
with the export. Without a separate witness, rewrite detection is limited to the
coverage established by verified external anchors; an unwitnessed, unanchored
suffix has internal-consistency evidence only. This is the substance of
`ERRATA-v0.1.md`.

## Layout

- `DSES-v0.1.md` and `dses-v0.1.schema.json`: sequence specification and event
  schema
- `DSES-v0.2.md`: outcome-evidence layer release candidate
- `IMPLEMENT.md`: external implementer route and version guidance
- `quickstart/`: passive and sealed sequence examples plus tiny helpers
- `IMPLEMENTATION-CHECKLIST.md`: pre-pilot evidence and governance checklist
- `FOUNDING-IMPLEMENTERS.md`: program criteria and evidence thresholds
- `ERRATA-v0.1.md`: correction to the v0.1 I2 claim
- `CLAIMS-CLASSIFICATION.md`: every v0.2 MUST classified as S, C, X, T, or A
- `schemas/`: four v0.2 JSON Schema 2020-12 schemas
- `artifacts/` and `examples/`: shipped outcome-layer definitions and worked
  evidence package
- `scripts/`, `rules/`, and `tests/`: reference implementation and gates

## Verified environments

`requirements.txt` pins direct dependencies only; the transitive closure is not
hash-pinned, for reasons and with the exact resolved sets recorded in
`ENVIRONMENTS.md`. The outcome-layer gate has been observed green on a Linux
container and on independent macOS hardware with a newer interpreter and a
differently resolved transitive set.

## Licensing

Two licenses apply, with directory-level scope stated explicitly.

- **Specification and documentation** (`DSES-v0.1.md`, `DSES-v0.2.md`,
  `ERRATA-v0.1.md`, `CLAIMS-CLASSIFICATION.md`, `README.md`, and implementation
  guides): CC BY 4.0. See `LICENSE-SPEC.md`.
- **Reference implementation** (`scripts/`, `rules/`, `tests/`, `schemas/`,
  `fixtures/`, `artifacts/`, `examples/`, `quickstart/`, and `run_all.sh`): MIT.
  See `LICENSE-CODE.md`.

## Publication boundary

This candidate is not the permanent `0.2.0`. RFC 3161 token parsing, independent
recomputation, and conformance-grade current-payload-disposition replay are
explicitly not implemented and do not support shipped conformance claims.
Before minting permanent schema identifiers, remaining external release steps
include contributor attribution, named protocol/cryptography and statistical
review, and clean-machine reproduction from the archive. These are not
represented as verifier-established properties.
