# DSES v0.2 outcome-evidence layer (0.2.0-rc8)

Release candidate for public comment. The permanent `0.2.0` schema `$id`s are minted once, at release, and never reused, so this candidate carries `0.2.0-rc8` until public comment closes. Extends DSES v0.1.0 as corrected by `ERRATA-v0.1.md`.

## Reproduce every claim in this package

```
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
bash run_all.sh
```

Build the clean publication archive with `python3 scripts/make_release.py`. The builder uses an explicit allowlist, excludes caches/review notes/nested archives, fixes member ordering and timestamps, and adds `RELEASE-MANIFEST.sha256` for the exact published bytes.

That runs six stages, in this order for a reason:

0. `scripts/check_jcs.py` fails fast on canonicalization vectors chosen to catch common non-RFC-8785 JSON number spellings.
1. `scripts/release_lint.py` checks the publication contract: implemented verifier rules exist and have rule-asserting fixtures, verifier rule/class labels agree with the claims table, every uppercase conformance keyword in the specification carries an explicit requirement tag, section numbering is coherent, and generated claim counts are current.
2. `scripts/validate_package.py` validates the SHIPPED v0.2 package envelope, cohort/case events, definition artifacts, and derived artifacts against four Draft 2020-12 schemas. The bundled v0.1 decision sequences receive structural checks here and full hash-chain/payload-commitment semantic replay in the verifier; they are not misdescribed as v0.2-schema-validated objects.
3. `scripts/dses_verify.py` is the reference verifier, run against the SHIPPED artifacts with the worked example's trust store supplied explicitly. It recomputes hashes, replays chains, verifies payload commitments including those of the bound v0.1 sequences, verifies RFC 9162 inclusion and consistency proofs, validates DSES-SIG-v1 profile/algorithm/context/target/key status for every signature it consumes, verifies anchor receipts only against the reader-supplied EXTERNAL trust store, executes the declared rule modules against their shipped fixtures, and recomputes every metric and required disclosure against snapshot-frozen evidence.
4. `tests/run_regression.py` runs the adversarial suite. Every verifier fixture asserts the SPECIFIC rule that must fire; cascading failures are allowed, so the suite does not overclaim that each mutation has only one possible rejection path.
5. Only then is the example regenerated into an isolated temporary copy (excluding `.venv`, VCS state, caches, and archives), never over the shipped files. This is a semantic regeneration check, not a claim of bit-for-bit deterministic archive reproduction.

## Trust anchors and witnesses

External anchor trust is never implicit. For the worked example, run `scripts/dses_verify.py --anchor-trust examples/anchor-trust-store.json`; a deployment verifier should supply its own trust policy/store. `--witness witness.json` can additionally compare a separately held checkpoint with the export. Without a separate witness, rewrite detection is limited to the per-chain coverage established by verified external anchors; an unwitnessed, unanchored suffix has internal-consistency evidence only. This is the substance of Erratum 1.

## Layout

- `DSES-v0.2.md` specification
- `ERRATA-v0.1.md` correction to the v0.1 I2 claim
- `CLAIMS-CLASSIFICATION.md` every MUST classified as S, C, X, T, or A
- `schemas/` four JSON Schema 2020-12 schemas, including the package envelope
- `artifacts/` shipped analytic definition-artifact instances; the schema also defines `secondary_use_governance` for individual-level secondary use, resolvable and hash-verified
- `examples/` the generated package, six derived metric artifacts, v0.1 decision sequences, example trust store, and nonce store
- `scripts/`, `tests/` reference implementation and adversarial suite

## Verified environments

`requirements.txt` pins direct dependencies only; the transitive closure is not hash-pinned, for reasons and with the exact resolved sets recorded in `ENVIRONMENTS.md`. The gate has been observed green on a Linux container and on independent macOS hardware with a newer interpreter and a differently resolved transitive set.

## Licensing

Two licenses, with directory-level scope stated explicitly so there is no ambiguity about which applies to what.

- **Specification and documentation** (`DSES-v0.2.md`, `ERRATA-v0.1.md`, `CLAIMS-CLASSIFICATION.md`, `README.md`): CC BY 4.0. See `LICENSE-SPEC.md`.
- **Reference implementation** (`scripts/`, `rules/`, `tests/`, `schemas/`, `fixtures/`, `artifacts/`, `examples/`, `run_all.sh`): MIT. See `LICENSE-CODE.md`.

## Publication boundary

This archive is a release candidate, not the permanent `0.2.0`. RFC 3161 token parsing, independent recomputation, and conformance-grade current-payload-disposition replay are explicitly not implemented and do not support shipped conformance claims. Before minting the permanent schema identifiers, the remaining external release steps are contributor attribution, an independent protocol/cryptography review, and clean-machine reproduction from the archive using the pinned dependency set. These are intentionally not represented as verifier-established properties.
