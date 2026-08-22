# CLAIMS-CLASSIFICATION

**Applies to:** DSES v0.2.0-rc8 (Release candidate for public comment)
**Status:** Normative companion to Annex D. Release-blocking: no requirement ships unclassified.

Two independent dimensions, kept separate because conflating them is itself a form of overclaiming.

**Verification class** answers: what kind of establishment is possible in principle?

| Class | Meaning |
|---|---|
| **S** | Schema-checkable |
| **C** | Cryptographically checkable from the package plus the external trust root |
| **X** | Cross-record checkable |
| **T** | Statistically assessable |
| **A** | Not mechanically established by DSES; the A-class aspect requires external or human attestation |

**Reference verifier support** answers: does this build actually perform it?

| Status | Meaning |
|---|---|
| **implemented** | The reference build enforces the requirement. Verifier-enforced requirements use a stable rule identifier and a regression fixture that asserts that rule fires; schema-only requirements are enforced by the normative schema and exercised by schema-rejection fixtures. |
| **partial** | performed under stated limits |
| **not_implemented** | specified, not yet checked by this build |
| **not applicable** | an attestation or external fact for which reference-verifier implementation is not meaningful |
| **out of scope** | intentionally outside DSES conformance verification |

A conformance statement MUST NOT assert an **A** requirement as established, and MUST NOT describe a **not_implemented** requirement as verified. "Implemented" never means merely described in prose: a machine-enforced check exists, and verifier rules are paired with a rule-asserting regression fixture.

---

## Section 3: cryptographic layer

| # | Requirement | Rule | Class | Support |
|---|---|---|---|---|
| 3.1a | Event hash equals SHA-256 of the RFC 8785 preimage | EVT-HASH | C | implemented |
| 3.1b | Artifact content hash recomputes | ART-HASH | C | implemented |
| 3.1c | Integers in hashed fields within the JCS-safe range | schema | S | implemented |
| 3.2a | Chain commits to the payload commitment, never the raw payload | EVT-HASH | C | implemented |
| 3.2b | Content commitment matches payload | PC-CONTENT | C | implemented |
| 3.2c | Low-entropy payloads use randomized hiding commitments | PC-HIDING | S + X | implemented |
| 3.2d | Hiding commitment matches payload under its nonce | PC-NONCE | C | implemented; checkable from the committed event, its payload, and the nonce sidecar. It does NOT depend on the external trust root (Section 3.6.1); a verifier without the sidecar verifies content commitments only |
| 3.2e | No copy of a destroyed nonce survives | none | **A** | not applicable |
| 3.2f | Available hiding nonce encoding matches `nonce_bits` and is at least 128 bits | PC-NONCE-LENGTH | X | implemented |
| 3.2g | Hiding nonce was unpredictably generated | none | **A** | not applicable |
| 3.3a | Checkpoint log is append-only head observations | CKPT-ROOT | C | implemented |
| 3.3b | Committed heads match the chains as exported | CKPT-HEAD | C | implemented |
| 3.3c | RFC 9162 consistency proof holds between epochs | CKPT-CONSIST | C | implemented |
| 3.3d | Checkpoint cadence within declared policy | CKPT-CADENCE | X | implemented |
| 3.4a | External anchoring derived from a receipt verifying under the EXTERNAL trust root | ANCHOR-RECEIPT | C | implemented (DSES-ANCHOR-v1; full A1 key-substitution attack is a fixture) |
| 3.4b | RFC 3161 token parsing | none | C | **not_implemented**; `anchor_profile: rfc3161` receipts are treated as unverified anchors |
| 3.4c | Anchor precedes the declared prespecification cutoff | ART-PRESPEC | X | implemented |
| 3.5 | Anchor evidence never inside the object it attests | ART-NOANCHOR | S + X | implemented |
| 3.6a | Signatures follow the declared DSES-SIG-v1 profile, algorithm, and context and cryptographically verify | SIG-PROFILE, SIG-VERIFY | S + C | implemented; owns only signatures against genesis-resolved keys, never anchor receipts (Section 3.8, rule ownership) |
| 3.6i | The DSES-SIG-v1 statement encoding matches the shipped test vectors | SIG-VECTORS | C | implemented |
| 3.8f | A verifier recomputes every code digest and conforms to shipped fixtures; executing the shipped modules is permitted, not required | RULE-DIGEST, RULE-CONFORM | C + X | implemented |
| 3.8g | Every executable reference carries a media type and an explicit locator for the bytes its digest covers | RULE-DIGEST, RULE-RESOLVE | S + C | implemented |
| 3.8h | Every constant a verifier needs is declared as data, and the reference module agrees with it | RULE-PARAMS | S + X | implemented |
| 6.11g | The charter declares its agreement statistic as an executable rule, and recomputation calls that rule | ADJ-AGREE | S + X | implemented |
| 6.11h | Independent assessments come from distinct adjudicators, and no assessment is cited twice | ADJ-INDEPENDENT | X | implemented |
| 6.11i | Every adjudication binds the criterion's charter directly | ADJ-CHARTER | S + X | implemented |
| 6.11j | Charters declare a revision protocol; assessment-free resolutions name an authorized decider and assert no agreement statistic | ADJ-DECIDER, ADJ-AGREE, ADJ-METHOD | S + X | implemented |
| 3.6b | Keys resolve ONLY from the committed genesis directory | KEY-COMMITTED | X | implemented |
| 3.6c | Signature targets the object it purports to cover | SIG-TARGET | C | implemented |
| 3.6d | Signing key usable at signing time | SIG-KEYTIME | X | implemented |
| 3.6e | Key custody | none | **A** | not applicable |
| 3.7 | No self-reported capability, assurance, state, or prespecification labels | DRV-NOLABEL, LINK-NOSTATE, schema | S + X | implemented |
| 3.8a | Code artifact digest equals the actual rule module bytes | RULE-DIGEST | C | implemented |
| 3.8b | Shipped rule fixtures pass against the loaded module | RULE-CONFORM | X | implemented |
| 3.8c | Derivation software digest equals the actual engine bytes | DRV-ENGINE | C | implemented |

## Section 4: definition artifacts

| # | Requirement | Rule | Class | Support |
|---|---|---|---|---|
| 4.2 | Every criterion carries a binary validity projection | schema | S | implemented |
| 4.3 | Every semantically consequential definition reference is pinned by identifier, version, and content hash | REF-RESOLVE, REF-HASH | S + X | implemented |

## Section 10: deployment obligations

| # | Requirement | Rule | Class | Support |
|---|---|---|---|---|
| 10.2 | An I2-or-above claimant makes a verifier and sample export available | none | **A** | not applicable |
| 10.3 | A deployment publishes its Evidentiary Considerations section | none | **A** | not applicable |

## Section 5: cohort chain

| # | Requirement | Rule | Class | Support |
|---|---|---|---|---|
| 5.1a | Manifest attestation signature verifies | SIG-VERIFY | C | implemented |
| 5.1b | Membership leaves unique across manifests | DENOM-UNIQUE | X | implemented |
| 5.1c | Manifest committed within declared latency | MAN-LATENCY | X | implemented |
| 5.1d | Manifest not curated before commitment | none | **A** | not applicable |
| 5.2a | Every committed position across all manifests has a track | DENOM-CLOSED | X | implemented |
| 5.2b | Track binds to its manifest by event hash | TRACK-MANIFEST | X | implemented |
| 5.2c | Inclusion proof verifies the carried leaf | TRACK-INCLUSION | C | implemented |
| 5.3a | Snapshot population root recomputes from shipped tuples | SNAP-ROOT | C | implemented |
| 5.3b | Snapshot tuples bind real heads at their sequences | SNAP-HEAD | C | implemented |
| 5.3c | Snapshot commits the preceding cohort head | SNAP-PREV | X | implemented |
| 5.3d | Snapshot definition versions equal the reconstructed in-force set | SNAP-INFORCE | X | implemented |
| 5.4 | Checkpoint coverage matches declared policy | CKPT-COVER | X | implemented |

## Section 6: case chains, v0.1 binding, adjudication

| # | Requirement | Rule | Class | Support |
|---|---|---|---|---|
| 6.1 | Track state replayed, never asserted | LINK-NOSTATE, LINK-ASSERT | S + X | implemented |
| 6.3a | Referenced v0.1 sequence resolves | V01-RESOLVE | X | implemented |
| 6.3b | v0.1 envelope replays as a valid hash chain | EVT-HASH | C | implemented |
| 6.3c | v0.1 payload commitments verify for every consumed event | PC-CONTENT | C | implemented (the demonstrated independence-class tamper is a fixture) |
| 6.3d | Bound head and final decision belong to the sequence | V01-HEAD, V01-FINAL | C | implemented |
| 6.3e | The declared projection rule executes over the sequence, establishing baseline-exposure-evaluation ordering | V01-PROJECT | X | implemented |
| 6.3f | Actor identity per the projection rule | V01-ACTOR | X | implemented |
| 6.3g | The originating v0.1 deployment's own integrity class | none | **A** / X | partial: read as declared; full verification needs that deployment's verifier receipt |
| 6.4 | Linkage accuracy rates correct | none | **A** | not applicable |
| 6.7a | Conclusion iff determinate | ADJ-CONCL | S + X | implemented |
| 6.7b | Criterion permitted by the cohort | ADJ-CRITERION | X | implemented |
| 6.10 | Revision lineage: one root, no forks, one active leaf, no laundered determinations | ADJ-LINEAGE, ADJ-FORK, ADJ-ACTIVE | X | implemented |
| 6.11a | Assessments pre-consensus and prior to their adjudication | ADJ-ASSESS | X | implemented |
| 6.11b | Adjudicators on the resolved charter roster | ADJ-ROSTER | X | implemented |
| 6.11c | Charter minimum assessments and permitted resolution method | ADJ-MIN, ADJ-METHOD | X | implemented |
| 6.11d | Inter-adjudicator agreement RECOMPUTED from pre-consensus assessments | ADJ-AGREE | X | implemented |
| 6.11e | Adjudicators actually blinded | none | **A** | not applicable |
| 6.11f | Maturation derived from index date, risk window, and cutoff | MAT-DERIVED | X | implemented |

## Sections 7 and 8: derived artifacts and metrics

| # | Requirement | Rule | Class | Support |
|---|---|---|---|---|
| 7.1 | No stored status or prespecification label | DRV-NOLABEL | S | implemented |
| 7.1b | Effective status replays from lifecycle events | DRV-LIFECYCLE | X | implemented |
| 7.1c | No active artifact depends on a superseded adjudication | DRV-STALE | X | implemented |
| 7.2 | Registered artifacts ship, hashes match, references resolve pinned | DRV-SHIPPED, DRV-HASH, REF-RESOLVE, REF-HASH | C + X | implemented |
| 7.3a | Metrics recompute by EXECUTING the declared rules against SNAPSHOT-TRUNCATED evidence | MET-RECOMPUTE | X | implemented |
| 7.3b | Committed input set equals the inputs the recomputation used | MET-INPUTS | X | implemented |
| 7.3c | Recomputation by a fully independent implementation | none | X | **not_implemented**; the verifier does not merely share primitives with the derivation engine, it calls the same `dses_derivation.recompute_metric` orchestration the generator called, over the same loaded rule modules and the same `dses_core` canonicalization. What the verifier establishes is that the declared rules, applied to snapshot-frozen evidence, reproduce the registered counts. It does not establish agreement between two independently written implementations, and no shipped claim says otherwise |
| 7.3d | Value consistent with recomputed counts | MET-ARITH | X | implemented |
| 8.7 | Declared interval recomputes over nonzero denominators | MET-INTERVAL | X | implemented |
| 8.11 | Interval conformance tolerance is declared as data, absolute, and stated once | RULE-PARAMS | S | implemented |
| 7.5 | Prespecification derived from plan, external anchor, and cutoff | MET-PRESPEC | X | implemented |
| 8.2 | `partially_correct` and `not_classifiable` are excluded by the declared binary projection and disclosed | MET-EXCL | X | implemented |
| 8.5 | Every required disclosure field is recomputed from snapshot-frozen evidence or pinned definition artifacts | MET-DISCLOSE, MET-BLIND, MET-EXCL | X | implemented |
| 8.9 | EAR declares an executable alignment relation, that relation is what recomputation uses, and it suits the criterion's declared answer-space semantics | MET-ALIGN | S + X | implemented |
| 8.10 | A metric's declared interval_method equals its declared estimator's method | MET-ESTIMATOR | X | implemented |
| 8.8 | How well an estimate characterizes reality | none | **T** / **A** | out of scope for any verifier: DSES establishes that the statistic was computed as declared, not that the estimand is well characterized |

## Sections 2, 9, 11, 12

| # | Requirement | Rule | Class | Support |
|---|---|---|---|---|
| 2.2 | Rewrite detection coverage-specific, per chain | CKPT-ANCHORED + coverage map | X | implemented |
| 2.3 | Claim tiering used correctly in prose | none | **A** | not applicable; attested by the author, not by the reviewing system, since all review of this build to date was machine review (see Review provenance, Section 13) |
| 2.4 | Threat model stated and claims scoped to it | none | **A** | not applicable |
| 9.3a | Every cohort declares its unit of analysis, prespecified and anchored | UOA-DECLARED | S + X | implemented |
| 9.3b | No metric is reported at a finer unit than the cohort authorises | UOA-MATCH | X | implemented |
| 9.3c | Individual-level derivation resolves an anchored secondary-use governance artifact | UOA-GOVERNANCE | S + X | implemented |
| 9.3d | Individual-level metrics meet the governance minimum cell size and ship an interval | UOA-CELLSIZE | S + X | implemented |
| 9.3e | Individual-level metrics disclose case mix as the governance requires | UOA-CASEMIX | S + X | implemented |
| 9.3l | Individual context covers every assigned subject decision instance in the window, not merely metric-eligible cases | UOA-CONTEXT, UOA-CONTEXT-POPULATION | X | implemented |
| 9.3m | Context breakdowns reconcile exactly to the instance count, and the metric-eligible subset is derivable | UOA-CONTEXT-RECONCILE, UOA-CONTEXT-METRIC | X | implemented |
| 9.3n | Individual derivation binds a prospective responsibility assignment artifact independent of linkage | UOA-ASSIGNMENT | S + X | implemented |
| 9.3o | Governance declares prospective or retrospective timing truthfully against its own anchor | UOA-TIMING | X | implemented |
| 9.3p | Case-mix disclosure is established; adjustment adequacy and any risk-adjusted claim are not mechanically established | UOA-CASEMIX | S + **A** | implemented as disclosure only |
| 9.3q | Privacy basis and professional identity mode are declared; validity of the legal basis is external | schema | S + **A** | implemented as declaration |
| 9.3r | Pseudonymous subject binding does not establish the civil identity of the professional | none | **A** | not applicable: identity attribution is an independently governed evidence dependency |
| 9.3f | No DSES artifact or conformance claim asserts a standard-of-care, reasonable-use, competence, negligence, legal-authority, admissibility, or adverse-action determination | UOA-NONORM | S | implemented |
| 9.3g | Every individual metric is recomputed only from trajectories whose baseline and evaluation actor equal its subject_ref, and every committed input belongs to that subject | UOA-SUBJECT | X | implemented |
| 9.3h | Every individual metric declares a bounded observation window within the governance maximum | UOA-WINDOW | S + X | implemented |
| 9.3i | Every individual metric carries balanced reliance context recomputed over the full bounded subject window | UOA-CONTEXT | X | implemented |
| 9.3j | High-stakes governance declares aggregate-only adverse action prohibited, case-level review required, subject notice/evidence access, and appeal | UOA-HIGHSTAKES | S | implemented |
| 9.3k | Discoverability, privilege, legal usability, legal authority, and sufficiency under external law are not established by DSES | none | **A** | out of scope |
| 9.4 | That a metric is used only for its declared purpose by its authorised recipients | none | **A** | not applicable: DSES records the declared purpose and recipients; it cannot enforce what a review body does with a number once disclosed |
| 9.4b | That a high-stakes review body actually performs the declared case review, notice/access, and appeal safeguards | none | **A** | not applicable |
| 9.5 | Adequacy of case-mix adjustment or any empirical/Bayesian reference distribution as a characterization of professional practice | none | **T** / **A** | out of scope for conformance verification |
| 9.1 | No privilege determination field | schema | S | implemented |
| 9.2 | Current payload disposition is replay-derived from integrity events | none | X | **not_implemented** in this build; initial disposition is recorded but no conformance-grade current-disposition replay is claimed |
| 11 | No conformant calculation depends on an unincorporated extension | schema + prose | S + **A** | partial: schema isolates extensions; dependence is attested |
| 12 | Profile conformance evaluated explicitly and reported | PROFILE block | X | implemented |

## Envelope and structural rules

| # | Requirement | Rule | Class | Support |
|---|---|---|---|---|
| 3.1d | Event identifiers unique within a chain | EVT-UNIQUE | X | implemented |
| 3.1e | Sequence numbers contiguous | CHAIN-SEQ | C | implemented |
| 3.1f | Genesis carries no predecessor | CHAIN-GENESIS | C | implemented |
| 3.1g | Each event links to its predecessor | CHAIN-LINK | C | implemented |
| 3.1h | Timestamps are real instants | EVT-TIME | X | implemented |
| 3.1i | Declared chain scope matches the chain | EVT-SCOPE | X | implemented |
| 3.1j | Chain references unique in the package | CHAIN-UNIQUE | X | implemented |
| 3.1k | Every event carries a payload commitment | PC-PRESENT | S | implemented |
| 3.6f | Exactly one cohort genesis event | GENESIS-ONE | X | implemented |
| 3.6g | Key references unique in the committed directory | KEY-UNIQUE | X | implemented |
| 3.4d | An external trust store is supplied before any anchor is credited | TRUST-EXTERNAL | X | implemented |
| 3.4e | No anchor credited from an authority the package declares distrusted | ANCHOR-DISTRUST | X | implemented |
| 3.8d | Declared rule identifiers resolve to shipped code | RULE-RESOLVE | X | implemented |
| 3.8e | Declared rules ship conformance fixtures | RULE-FIXTURES | X | implemented |
| 4.1 | Every artifact identity resolves to exactly one content digest at a version | ART-UNIQUE | X | implemented |
| 5.1e | At least one eligibility manifest is committed | MAN-PRESENT | X | implemented |
| 5.2d | Case chain genesis is a case track | TRACK-GENESIS | X | implemented |
| 5.2e | Inclusion proof targets its own manifest's committed root | TRACK-ROOT | C | implemented |
| 5.3e | Snapshot population covers every track | SNAP-COVER | X | implemented |
| 6.1a | Linkage attempted only from a non-terminal state | LINK-ORDER | X | implemented |
| 6.3h | v0.1 events structurally well formed with payload commitments | V01-SHAPE | S | implemented |
| 6.10a | Revision cites an adjudication resolvable in the same chain | ADJ-REVREF | X | implemented |
| 6.10b | Exactly one active adjudication per case and criterion | ADJ-ACTIVE | X | implemented |
| 6.13 | Status recorded under the primary criterion for every linked case | OL-STATUS | X | implemented |
| 6.14 | Every mature linked case carries an active adjudication | OL-ADJUDICATED | X | implemented |
| 7.2a | Registered derived artifact resolves to a committed snapshot | DRV-SNAP | X | implemented |
| 2.2a | Witness, when supplied, matches the exported checkpoint | CKPT-WITNESS | C | implemented |
| 10.1 | A structurally unprocessable package yields a verdict, never a stack trace | PKG-MALFORMED | X | implemented |


---

## Counts

Verification class: **S** 31, **C** 30, **X** 85, **T** 2, **A** 20.
Reference verifier support: **implemented** 120, **partial** 2, **not_implemented** 3, **not applicable** 13, **out of scope** 3.

The requirements marked **not_implemented** are named explicitly in the specification and do not support any shipped conformance claim.

The reference verifier reads every A-bearing row in this file and prints that normative attestation inventory on every run; no hand-maintained list is duplicated here. Verification-class counts are **label counts**, not mutually exclusive row counts: a mixed row such as `S + X` contributes to both columns. Counts are generated by `scripts/release_lint.py --emit-counts` and checked on every build.
