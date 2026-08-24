# DSES Governance

Version 1.0, August 2026. How this specification changes, and who decides.

## Stewardship

DSES is stewarded by its originating maintainer, Joshua M. Henderson (Evidify
LLC). Evidify is the originating maintainer of DSES and builds the assurance,
conformance, and evidence infrastructure around it. Stewardship will move
toward shared governance (a technical advisory group, eventually possibly an
independent body) as independent implementations and organizational adopters
exist; it will not be transferred before the standard has proven its category.

## Change classes

- **Editorial** (typos, clarity, non-normative examples): maintainer merge,
  patch release.
- **Normative clarification** (resolves ambiguity without changing what
  verifies): requires an issue documenting the ambiguity, ideally from an
  implementation report; minor release.
- **Normative change** (changes what verifies): requires a concrete
  counterexample, internal contradiction, or interoperability failure; a new
  or updated adversarial fixture; and a claims-classification row. Minor
  release if additive, major if it invalidates previously conformant
  packages.
- **Architecture change** (event model, canonicalization, commitment or
  signature profiles, Merkle and anchoring semantics, snapshot
  recomputation): frozen. Reopened only by demonstrated soundness defect.

## Versioning and compatibility

Semantic versioning against verification behavior: a package conformant under
X.Y remains conformant under X.Y' for Y' > Y. Identifiers ($id URLs, DOIs)
are permanent once a version is minted; release candidates carry rcN and may
change. Verification transcripts always name the exact version and archive
hash they ran against.

## Disputes

Technical disputes are resolved by evidence: a fixture, a package, or a
contradiction in the text. Where evidence is genuinely unavailable, the
maintainer decides and records the rationale in the changelog. Claims about
what DSES establishes are governed by CLAIMS-CLASSIFICATION.md; a dispute
about whether something is established is answered by its verification class.
