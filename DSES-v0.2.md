# Decision-Sequence Evidence Schema (DSES)
## Part II: The Outcome-Evidence Layer

**Version:** 0.2.0-rc8 (Release candidate for public comment)
**Date:** August 20, 2026
**Author:** Joshua M. Henderson, Ph.D. (Evidify LLC, East Orange, NJ)
**Status:** Open specification. Comments and implementation reports welcome.
**Specification license:** CC BY 4.0. **Reference implementation license:** MIT.
**Extends:** DSES v0.1.0 (August 15, 2026) as corrected by ERRATA-v0.1 (Erratum 1, the I2 detection claim).

---

## Abstract

DSES v0.1 records the trajectory of a human-AI decision. A v0.1 record is complete and conformant regardless of whether any judgment in it was correct: it records sequence, not correctness, and says so. This document defines the layer that binds sealed decision trajectories to evidence about correctness (observed outcomes, adjudicated reference evidence, and derived validity classifications) without collapsing the distinctions between them. An observed outcome is not a reference determination. A reference determination is not truth. A validity classification is not a causal claim. DSES defines an open, vendor-neutral evidentiary representation for this binding.

The organizing discipline is the verifier question: **given only a purported DSES package and the declared external trust anchors, what exact claims can a hostile third-party verifier mechanically establish, and which remain attestations?** Every normative requirement is classified against that question in `CLAIMS-CLASSIFICATION.md`, and the reference verifier prints its attestation list on every run.

Six protocol invariants govern this specification:

1. Nothing contains the evidence that proves its own hash. Anchors and signatures live outside the objects they attest.
2. Every evolving state is an event. No field is mutated after commitment.
3. Every Merkle tree has exactly one purpose: membership, append-only history, or population snapshot. The three are never mixed.
4. Every member of a committed population gets a track before linkage is attempted, including the ones that never link.
5. No prose says the verifier establishes a claim until a check and a test fixture exist for it.
6. No descriptive label is stored as a primary fact when it can be derived. Store evidence; derive the label. The design test is to delete every label in a package (anchored, prespecified, linked, validated, conformant) and ask whether a hostile verifier can reconstruct it from what remains.

---

## 1. Claims as a dependency DAG

Claims form a directed acyclic graph. Every claim declares its **highest claim layer** and enumerates its evidence dependencies on lower layers.

| Layer | Name | What it establishes |
|---|---|---|
| 1 | Sequence evidence | A designated human decision state was committed before the recorded or mechanically gated presentation of specified AI information through the instrumented pathway (v0.1, with independence classes per v0.1 Section 6). |
| 2 | Outcome and reference evidence | What was later observed, and what a versioned adjudication process concluded about the evaluation target at the defined index time. |
| 3 | Validity inference | Classification of a decision against a named, versioned evaluation criterion. Derived, recomputable, never primary; assurance bounded by its dependencies. |
| 4 | Causal inference | Requires an identification strategy external to this specification. Out of scope, permanently. |

Terminology rules (normative): AI attribution uses **"AI-associated revision"** or **"post-exposure revision toward AI"**. "AI-caused" and equivalents are prohibited absent a documented Layer 4 design. "Independent" carries a v0.1 independence class or does not appear.

### 1.1 Scope: criterion-evaluable tasks

This layer applies to tasks for which an immutable `evaluation_criterion` can be stated. The criterion abstraction is general and is implemented as such in the schema: `criterion_type` selects a specialization, of which `clinical_reference_standard` is one, `policy_rule` and `benchmark` are others. Tasks with no defensible criterion (contested preference allocations, value tradeoffs) are outside this layer, and applying it to them is non-conformant. v0.1 remains domain-neutral; v0.2 adds a criterion-evaluable module on top of it.

---

## 2. Evidentiary considerations (normative)

Every conformant deployment MUST include an Evidentiary Considerations statement incorporating this section and Section 2.4. <!-- req:10.3 -->

### 2.1 What the mechanisms establish

Within declared and verifier-confirmed capabilities: that a byte string existed no later than an externally anchored time, where an anchor exists and verifies; that a chain is internally consistent, and relative to a previously witnessed checkpoint has not been rewritten since; that record B references record A, that a key signed a named target hash under a named context, that an inclusion proof places a leaf in a committed tree, and that a consistency proof shows one committed tree extends another; and, at v0.1 I3(a), that AI output release was mechanically predicated on a prior committed decision state.

### 2.2 What the mechanisms do not establish

Everything in v0.1 Section 7's non-claims, plus:

- **an unwitnessed hash chain does not establish historical immutability against its own operator.** An operator controlling the complete history can rewrite an event and recompute every downstream hash, commitment, checkpoint root, consistency proof, and snapshot root; the resulting package is internally perfect and an offline verifier holding only it will verify it. Detection requires a trust anchor outside the operator. This is Erratum 1, and it ships as an executable regression fixture: the suite requires that the unwitnessed run of a fully consistent rewrite is not reported as detected;
- a hash of low-entropy content does not conceal it (Section 3.2);
- a schema-valid package is not a conformant package (Section 10).

### 2.3 Prevented, checkpoint-relative, made visible

**Prevented** (violation detectable from the package plus declared anchors): storage of derived values that fail recomputation; assertion of capability flags the verifier cannot derive; publication of a metric without a resolvable snapshot; a linkage assertion with no successful attempt; a committed population member with no track.

**Checkpoint-relative** (detectable only against a previously witnessed commitment): silent modification or erasure after a witnessed checkpoint; narrowing of a membership-committed denominator after its commitment was witnessed; backdating of definition artifacts relative to their anchor.

**Made visible, not prevented**: curation of the eligible population before commitment; charter or adjudicator shopping among precommitted alternatives; strategic censoring mislabeled as loss to follow-up; blinding breaches omitted from the recorded information set; selective emphasis among analyses. No DSES statement may imply otherwise.

### 2.4 Threat model (normative)

Claims in this specification are stated against these adversaries:

| | Adversary | Assumed capability |
|---|---|---|
| A1 | Deploying operator | Can rewrite all local storage and recompute every internal hash |
| A2 | Deploying operator | Controls local clocks and ingestion timing |
| A3 | Deploying operator | Cannot forge signatures of an external timestamp authority or transparency log |
| A4 | Outcome source | May be erroneous or incomplete; not assumed malicious |
| A5 | Adjudicator | May violate blinding without recording it |
| A6 | Adjudicator and site | May collude |
| A7 | External anchor | May equivocate, or its keys may later be compromised |

Consequently: "externally anchored establishes existence before time T" holds **against the deploying operator, under the declared external-anchor trust model**, not unconditionally. A7 is why anchor diversity and monitoring are recommended and why the verifier reports anchor trust as an attestation rather than a verified property.

---

## 3. Cryptographic layer

### 3.1 Hashing, canonicalization, preimages

v0.2 protocol hashing is **SHA-256 only**. Protocol hashes (event hashes, predecessor hashes, Merkle roots and paths, chain head references) are bare lowercase hex strings; algorithm-tagged `{alg, digest}` objects are used for content and artifact digests, where future agility will be needed. This is one story, stated plainly, rather than agility asserted in prose and absent from the schema.

Preimages are defined explicitly:

- **Event hash:** SHA-256 of the RFC 8785 canonical form of the event with `integrity.event_hash`, all `signatures`, and the optional `payload` removed. `prev_event_hash` is inside the preimage.
- **Artifact content hash:** SHA-256 of the RFC 8785 canonical form of the artifact with `content_hash` removed. Anchor evidence is prohibited inside artifacts (Section 3.5), so there is no fixed point.
- **Merkle:** RFC 6962/9162 construction with domain separation, leaf hash H(0x00 || leaf) and interior node H(0x01 || left || right), inclusion proofs carrying leaf index and tree size, consistency proofs per RFC 9162 Section 2.1.4.

RFC 8785 canonicalization is REQUIRED for every event and artifact hash preimage. <!-- req:3.1a req:3.1b -->

Integers in hashed fields MUST lie within the JCS-safe range (schema-enforced); quantities that can exceed it are carried as decimal strings. <!-- req:3.1c -->

### 3.2 Two-level events, commitments, and payload disposition

Every event separates the chained **envelope and `payload_commitment`** from the **payload**, which may be available, archived, or destroyed.

`commitment_type` is `content_digest` or `hiding`. **`hiding` is REQUIRED where the payload's plausible value space is small enough to enumerate**, and is schema-enforced for `adjudicator_assessment_committed` and `reference_standard_adjudicated`, the two event types whose payloads are always low-entropy. <!-- req:3.2c -->

For an available hiding payload, the encoded nonce MUST match the declared `nonce_bits` and contain at least 128 bits. <!-- req:3.2f --> The nonce MUST have been generated unpredictably; DSES can verify its encoded length and binding, but not the quality of the randomness source, so generation unpredictability remains an A-class deployment attestation. <!-- req:3.2g --> A hiding commitment is SHA-256 over `nonce || RFC8785(payload)`. The term is **nonce**, not salt: this is a randomized hiding commitment, not password salting.

The security claim is stated exactly: *a hiding commitment prevents practical dictionary enumeration from the commitment alone, assuming the nonce is unavailable to the attacker.* DSES can record that nonce destruction was asserted; it cannot prove no copy survived (Section 2.4, A1).

`initial_payload_disposition` records disposition at creation and is never rewritten. The protocol represents later disposition changes through `outcome_integrity_event` records. A conformance-grade replay of current disposition is specified but **not implemented in this reference build** and therefore supports no v0.2.0-rc8 conformance claim. <!-- req:9.2 -->

### 3.3 Three tiers, and one append-only checkpoint log

The architecture is a cohort governance chain, per-case track chains, and a checkpoint log.

The checkpoint log is **append-only over head observations**, not a tree over current heads. Each leaf is the RFC 8785 canonical form of `{chain_ref, head_sequence, head_hash, checkpoint_epoch}`. When a case chain advances, a new observation is appended; no leaf is ever replaced. This is what makes RFC 9162 consistency proofs applicable: a proof that the newer tree extends the older one is only meaningful if the first *m* leaves are unchanged. A tree over mutable current heads cannot support such a proof, and the earlier draft that described one was wrong.

Append-only integrity is not coverage. A log that faithfully appends observations for eleven of twelve tracks is perfectly append-only and silently omits a case, so the cohort declares a `checkpoint_policy` and each checkpoint carries a coverage block that the verifier recomputes against the tracks actually present. Log integrity and population coverage are reported as separate claims.

Each `checkpoint_committed` event carries the head observations appended at that epoch, so the root is recomputable offline, and the verifier binds each committed head to the actual event at that sequence in the exported chain. Deployments above the inline threshold carry per-case inclusion proofs instead of inline observations.

### 3.4 Prespecification assurance and cutoffs

`prespecification_assurance` is graded: `declared`, `checkpoint_relative`, `externally_anchored`. Grade alone is insufficient, because ingestion timing is under operator control (A2): declaring an artifact prospective because no `outcome_observed` had yet been ingested proves nothing about whether outcomes had already occurred and been reviewed outside DSES.

Prespecification is therefore judged against a **declared external cutoff**, and every definition artifact carries one: `before_first_enrollment`, `before_first_ai_exposure`, `before_enrollment_close`, `before_earliest_outcome_maturation`, `before_data_access_unlock`, or `before_analysis_dataset_release`. The verifier compares anchor time to cutoff time. `post_hoc` is not a boolean; it is a relation to a named cutoff.

### 3.4.1 Anchoring is derived, and the trust root is external

An anchor is evidence, so the event that carries it is named `anchor_evidence_recorded`, not `artifact_anchored`. Recording evidence is not the same as being anchored: the verifier derives external anchoring only when a receipt cryptographically verifies, binds the exact artifact hash, anchor time, and authority together, and verifies under a key the READER supplies from outside the package. An `anchor_ref` string that merely claims to be a timestamp token establishes nothing and is derived as `asserted_unverified`.

**The trust root is external, and this is the whole point.** The threat model grants the deploying operator the power to rewrite everything local, including the genesis key directory. A verifier that resolved the anchor authority's public key from inside the package would therefore prove only that some key the package nominates signed the receipt, which is worthless against A1: the operator rewrites genesis, substitutes their own key under the same authority name, re-mints every receipt, and rebuilds the internally consistent history. The reference verifier consequently takes an external trust store (`--anchor-trust`) that binds authority identity to public key outside the package, and NEVER authenticates an anchor receipt against package-carried key material. The genesis directory may carry a copy of the authority key for information; matching key bytes do not create trust, because anchor authority is derived exclusively from the reader-supplied external trust store. The adversarial suite includes the full-strength version of this attack, with the genesis key substituted, every receipt re-minted, and every hash rebuilt, and asserts that it dies at the receipt-verification rule.

v0.2 defines DSES-ANCHOR-v1, a signed receipt over the canonical triple of artifact hash, anchor time, and authority identity, which the reference verifier checks. RFC 3161 token parsing is a second profile, specified but **not implemented in this build**; packages using it are treated as carrying unverified anchors. Anchor distrust is itself event-sourced (`anchor_distrusted`, with key compromise and equivocation as reasons), because the epistemic-revision problem solved for adjudications applies equally to trust anchors: an analysis must not retain an anchoring characterization after the basis for it collapses.

### 3.5 Anchors live outside what they anchor

An RFC 3161 request carries the hash of the datum being timestamped. If the returned token were then stored inside the artifact, the artifact's hash would change and the token would no longer attest it. Anchor evidence is therefore carried in `anchor_evidence_recorded` events referencing the artifact hash, never inside the artifact, and this is schema-enforced. An artifact can move from `declared` to `externally_anchored` without changing identity, which is the correct separation of concerns: improving evidence about an object should not create a different object.

### 3.6 Signature profile: DSES-SIG-v1

Signatures cover a domain-separated, length-prefixed statement over one named context and one named target hash. The encoding is normative and fully specified here, because an implementation that guesses it wrong does not get a diagnostic: every signature in a conformant package fails and the verifier reports forgery.

```
statement = "DSES-SIG-v1"                      US-ASCII, 11 bytes, no terminator
          || 0x00                              single separator byte
          || uint16be(len(context_label))      2 bytes, big-endian
          || context_label                     US-ASCII bytes of the label
          || uint16be(len(target_hash_hex))    2 bytes, big-endian
          || target_hash_hex                   LOWERCASE HEX ASCII, 64 bytes for SHA-256
```

Two points where an implementer would otherwise have to guess, stated explicitly. Lengths are unsigned 16-bit big-endian, not varints and not decimal ASCII. The target hash enters as its lowercase hex ASCII spelling, 64 bytes for SHA-256, **not** as the 32 raw bytes it denotes. `alg` is `ed25519` in v0.2, and the signature is over `statement` directly with no pre-hash.

`fixtures/dses-sig-v1.testvectors.json` ships a published private key seed, its public key, and for every context both the exact `signing_input` bytes in hex and a valid signature. An implementation that reproduces those bytes has the encoding right. The reference verifier self-tests against these vectors before it examines any package, under rule `SIG-VECTORS`, so a broken canonicalization or encoding is reported as such rather than as a package-level forgery.

Keys are resolved from the `key_directory` committed in the `cohort_chain_created` genesis event, with optional validity windows, rotation, and revocation. The anchor authority key is deliberately **not** resolvable this way; see Section 3.4.1.

**Contexts and what each target hash covers.** Seven contexts are defined in v0.2. What a signature means depends entirely on what its target commits to, so each is specified rather than left to inference:

| `context_label` | `target_hash` is the SHA-256 of |
|---|---|
| `event` | the event hash, as defined in Section 3.1 (the RFC 8785 preimage with `integrity.event_hash`, `signatures`, and `payload` removed) |
| `export-head` | the head event hash of the cohort chain at export |
| `eligibility-manifest` | the RFC 8785 canonical form of the manifest payload with `attestation_signature` removed |
| `checkpoint` | the event hash of the `checkpoint_committed` event |
| `assessment` | the event hash of the `adjudicator_assessment_committed` event |
| `anchor-receipt` | the RFC 8785 canonical form of `{artifact_hash, anchor_time, tsa_identity}`, the anchor receipt body (Section 3.4.1) |
| `v0.1-verification` | the head event hash of a verified DSES v0.1 decision sequence, for deployments that ship verifier receipts under requirement 6.3g |

Signatures are excluded from the event hash preimage and cover the event hash, which is why the exclusion is safe. Key custody remains an attestation: cryptography establishes that a key signed, not who held it.

### 3.6.1 Nonce transport

Randomized hiding commitments require the nonce to verify, and the commitment object deliberately does not carry it: a nonce inside the committed object would defeat the hiding property it exists to provide. Nonces travel in a **sidecar**, `examples/nonce-store.json` in this package, colocated with the payloads whose confidentiality they protect and destroyed with them. The sidecar has its own schema, `dses-v0.2-nonce-sidecar.schema.json`, and is keyed by **event hash** <!-- req:3.2f -->, not by `event_id`: event identifiers are unique only within a chain, so an id-keyed sidecar cannot unambiguously represent two events that share an identifier across chains. The event hash is already a cryptographic identity and commits to the payload commitment the nonce opens.

This has a classification consequence that rc4 corrects. Requirement 3.2d is checkable from the committed event, its payload, and the nonce sidecar <!-- req:3.2d -->. It does **not** depend on the external trust root: establishing that a hiding commitment matches an available payload under its nonce is pure cryptography, and no timestamp authority is involved. External trust evidence is required for the separate and later claim that the commitment existed before an anchored time. Keeping those dependencies distinct matters here more than most places, since this specification exists to keep evidence dependencies precise. A recipient who holds the package but not the sidecar can verify every content commitment and no hiding commitment, which is the intended graded disclosure, not a failure. A conformance statement that claims hiding commitments were verified MUST therefore state that the sidecar was available to the verifier. <!-- req:3.2d -->

### 3.7 No self-reported assurance

Events carry an integrity class, which is a deployment configuration claim, and nothing else about their own trustworthiness. Capability flags, rewrite-detection grades, prespecification grades, track states, and derived-artifact statuses are all **derived by the verifier** and are schema-prohibited as stored fields. Self-certified assurance is precisely the practice DSES exists to replace, and a specification that accepted it in its own records would be incoherent.

Rewrite detection in particular is **coverage-specific, not global**. An anchored checkpoint protects only the head observations included under it. The verifier therefore emits a coverage map: for each chain, the highest sequence witnessed under a verified anchor, with the epoch and anchor time. Events beyond that sequence are reported as not yet covered. A package-level badge would be false for exactly the newest evidence, which is usually the evidence a reader most wants to trust.

### 3.8 Executable rules are code, and their digests are normative

Any rule that affects deterministic recomputation carries a `rule_id`, a `code_artifact_digest` that is the SHA-256 of the ACTUAL rule module bytes, and a `fixtures_ref` naming shipped conformance test vectors. A digest of the rule's name is a content-addressed label masquerading as provenance and is a conformance failure. Every executable reference MUST also carry a `code_artifact` giving the media type and an explicit **locator** for the bytes the digest covers <!-- req:3.8g -->, and MUST carry as `parameters` any constant a verifier needs in order to check the rule <!-- req:3.8h -->. A constant that lives only in one implementation's source is the same defect as a digest without a locator: it tells a second implementation what to check but not where to read it, and rc3 reintroduced exactly that by placing answer-space requirements, interval methods, levels, tolerances, and quantiles in Python module constants with no data field. Declared parameters are authoritative; the reference module must agree with them, and the verifier checks that agreement under `RULE-PARAMS`. A digest without a locator answers "what hash" but not "of which object", and a second implementation would have to reverse-engineer a path convention private to one implementation, which is the same defect class as the signature-encoding gap.

The requirement on a verifier is precise, and it changed in rc4 because the previous wording made an independent implementation impossible. A conformant verifier MUST recompute every declared `code_artifact_digest` from the shipped bytes and MUST reproduce the behaviour the shipped conformance fixtures specify. <!-- req:3.8f --> It MAY do so by loading and executing the declared modules, which is what the reference verifier does, or by implementing the declared semantics natively in any language and demonstrating conformance against the same fixtures. Requiring execution of shipped Python would have made Section 3.8 and requirement 7.3c mutually exclusive: the rule that makes the reference trustworthy would have been the rule that forbids a second implementation. The model is therefore: **the declared rule semantics are normative, the content-addressed module is a reference realization, and the shipped fixtures are mandatory interoperability vectors.** Fixtures are not claimed to define the semantics; a finite vector set cannot uniquely determine a program, and two implementations can pass every vector and still diverge on an untested input. What the fixtures do is make divergence detectable at the points the specification cares about most, and make conformance testable without an interpreter. Where prose and fixtures disagree, the prose semantics govern and the disagreement is a defect in this document.

This is why fixtures are normative artifacts rather than developer conveniences. A rule that ships no fixtures cannot be conformed to by anyone who does not run its exact code, and the verifier rejects that under `RULE-FIXTURES`.

The reference implementation ships rules as Python modules under `rules/`; other packagings (OCI image digests, wheel hashes, WASM modules) are valid digest targets that this build does not execute.

**Rule ownership when several checks could fire.** Where a defect could plausibly violate more than one requirement, the specification, not the implementation, decides which rule owns it, because otherwise two conformant verifiers disagree about what a package did wrong. Two cases are settled explicitly. An anchor receipt that fails verification is always `ANCHOR-RECEIPT` (3.4a), never `SIG-VERIFY` (3.6a), because the receipt failed against the external trust root rather than against the committed key directory; `SIG-VERIFY` owns only signatures evaluated against keys resolved from genesis. A payload that has been altered under a stale commitment is always `PC-CONTENT` or `PC-NONCE` (3.2b, 3.2d), never `EVT-HASH` (3.1a), because the envelope hash is computed over a preimage from which the payload is excluded and is therefore undisturbed by the alteration.

---

## 4. Definition artifacts

Seven definition-artifact kinds are used by this layer: the six analytic kinds below plus `secondary_use_governance` for individual-level secondary use. All are immutable once referenced, content-addressed, anchor-free, and carry a prespecification cutoff. The six analytic kinds are: `cohort_definition`, `evaluation_criterion`, `adjudication_charter`, `metric_definition`, `analysis_plan`, `projection_rule`.

`evaluation_criterion` is the general abstraction, with `clinical_reference_standard`, `policy_rule`, and `benchmark` specializations. The clinical specialization decomposes the reference standard into four orthogonal axes rather than one conflated enum: `evidence_sources[]`, `timing`, `composition`, and `determination_mechanism`. A delayed composite panel-adjudicated pathology-containing standard is representable without extension.

Every criterion MUST carry a **`binary_validity_projection`** naming which validity states count as correct, which as incorrect, and which are excluded, because the reliance metrics are only defined over a binary partition (Section 8.2). <!-- req:4.2 -->

`projection_rule` is first-class because projection selection decides which committed state is the baseline, which exposure is the AI, and which state is evaluated. It carries baseline and target-exposure selection, `evaluation_state`, coexposure handling, the actor identity requirement, and a **machine-executable rule reference**: a rule identifier, a code artifact digest, and conformance fixtures. The same requirement applies to eligibility rules, decision rules, alignment relations, and estimators: anything subject to deterministic recomputation carries an executable identifier and fixtures, and prose accompanies but never substitutes.

---

## 5. Cohort chain

Events: `cohort_chain_created`, `anchor_evidence_recorded`, `anchor_distrusted`, `key_rotated`, `key_revoked`, `key_compromise_declared`, `eligibility_manifest_committed`, `definition_set_amended`, `checkpoint_committed`, `analysis_snapshot_committed`, `derived_artifact_registered`, `derived_artifact_superseded`, `derived_artifact_invalidated`, `outcome_integrity_event`.

### 5.0 Membership multiplicity

Membership leaves MUST be unique across the cohort's committed manifests. <!-- req:5.1b --> v0.2.0-rc8 supports only `unique_decision_instance`: each eligible decision instance receives its own pseudonymous membership token. Repeated encounters are represented as distinct eligible decision instances, never by repeating one token. A tree containing a repeated token can yield valid inclusion proofs while silently overstating the number of distinct committed instances, so `declared_multiplicity` is intentionally not a v0.2 option.

### 5.1 Manifests

Membership commitment (RFC 9162 tree over pseudonymous membership tokens, with declared token scheme and leaf encoding) is REQUIRED for OL; a count-only manifest supports only OL-declared. <!-- req:12 --> Manifest curation before commitment remains undetectable (Section 2.3). Near-encounter-time commitment MUST satisfy the declared manifest latency policy. <!-- req:5.1c -->

### 5.2 Snapshots

A snapshot commits `as_of_time`, `cohort_chain_head_before_snapshot` (the head *preceding* the snapshot event, which avoids the fixed point of committing to one's own hash), a **single population commitment** over canonical `{case_ref, chain_ref, case_chain_head, case_chain_sequence}` tuples, every definition version in force, and the deriving software digest. Two separate roots over cases and heads would prove both sets existed without proving the pairing; one tree over tuples proves the pairing, which is the thing a recomputation needs. Every published metric MUST reference a resolvable snapshot. <!-- req:7.2a -->

### 5.3 Amendments and integrity

`definition_set_amended` carries the artifact reference and a `cutoff_relation` (Section 3.4). `outcome_integrity_event` records exports, verifications, anchor publications, detected gaps, payload dispositions, and nonce destruction.

---

## 6. Case track chains

### 6.1 Track state is replayed, never asserted

`linkage_attempted` records an attempt *result* only. The track's state is replayed from the sequence of attempts and is schema-prohibited as a stored field, because a record carrying both a result and a state can assert that a failed attempt produced a linked track. Evolving state is replayed, never asserted alongside its own evidence.

### 6.2 Every member gets a track

A case chain's genesis is `case_track_created`, not `linkage_asserted`. It carries the **membership leaf itself** plus its inclusion proof, so the proof is self-contained: without the leaf value a verifier can only conclude that some unknown leaf existed at some index. Tracks then progress through `linkage_attempted` with results `linked`, `ambiguous`, `failed`, `decision_record_missing`, `outcome_record_missing`, or `withdrawn`. Only a successful attempt permits `linkage_asserted`.

### 6.3 Binding to a v0.1 decision sequence

`linkage_asserted` carries a `decision_sequence_ref`: version, sequence head hash, final decision hash, a resolver locator, and the declared integrity class of the originating deployment. The verifier **resolves and replays** that sequence: it recomputes every event hash, checks chain continuity, **verifies every payload commitment** (the event hash deliberately commits to the payload commitment rather than the raw payload, so replaying the envelope without checking commitments would verify a container while trusting its contents, and the contents are exactly what the metric engine consumes: baseline judgment, AI output, evaluation judgment, actor, exposure class, independence class), confirms the bound head hash is the sequence head, confirms the bound final decision belongs to that sequence and terminates it, confirms that the baseline judgment precedes AI exposure which precedes the evaluation state, and confirms the actor identity condition the projection rule requires. An unresolvable or non-replaying reference is a conformance failure, not a warning. Without this, v0.2 would bind outcomes to a claimed hash of a trajectory rather than to a trajectory, which is the thing the layer exists to prevent. The originating deployment's own integrity class remains partly attested: verifying it fully requires a verification receipt from that deployment's v0.1 verifier, which the schema accommodates and this build does not require.

### 6.4 Linkage accuracy

carries method, validation status, estimated false-match and false-nonmatch rates, and clerical review, because "deterministic" is a method, not a quality.

### 6.5 Linkage security

uses method-specific descriptors, not one narrative field. `pprl_secure_mpc` requires protocol, threat model, party count, collusion threshold, declared leakage, and implementation reference, because a method name is not a security property. `ttp_deterministic` requires the TTP identity, governance reference, crosswalk location, and a threat-model note. `pprl_bloom` requires the verbatim cryptanalysis disclosure.

### 6.6 External source provenance

uses a capability descriptor (authenticity, immutability, signature, timestamp assurance, revision history). DSES integrity classes describe DSES recording pathways and are not applied to external systems.

### 6.7 Adjudication

separates `conclusion_status` (determinate, indeterminate, not_assessable), `process_flags[]`, and lifecycle. A determinate conclusion reached under a charter deviation is representable; forcing a choice between recording the conclusion and recording the defect was the failure mode.

### 6.8 Revision is a new event, not a nested payload

A revised determination is a new `reference_standard_adjudicated` event carrying `revises_event_hash` and a reason. Each determination therefore has its own event identity, which is what downstream `adjudication_ref` fields need; a nested adjudication inside a revision event has no hash of its own to reference.

### 6.9 Status is per criterion

`linkage_status_updated` carries `followup_state` plus per-criterion `maturation_state` and `adjudication_state`, so a case can be adjudicated under the 30-day criterion and immature under the 1-year one, and intercurrent flags separate from censoring.

### 6.10 Adjudication lineage is a DAG, and physical order is never truth

For each case and criterion there is exactly one root adjudication; every later determination MUST cite the currently active predecessor through `revises_event_hash`; <!-- req:6.10 req:6.10a --> forks and cycles are conformance failures; the active adjudication is the unique leaf. A fresh determination appended without lineage is rejected, because "last event wins" would let an operator launder a replacement conclusion without ever declaring a revision.

### 6.11 The charter is enforced, not decorative

The verifier resolves every assessment's charter reference, requires assessing adjudicators to appear on the resolved roster, requires the charter's minimum number of independent pre-consensus assessments, requires the resolution method to be one the charter permits, and RECOMPUTES the recorded inter-adjudicator agreement from the pre-consensus assessment payloads. Maturation is likewise derived, not read: the verifier resolves the index event's timestamp from the replayed v0.1 sequence, adds the criterion's risk window, compares the data-availability cutoff, and rejects a recorded maturation state that contradicts the dates. Manifest latency and checkpoint cadence are checked against the cohort's declared policies for the same reason: a declared cadence that is never measured is a stored label.

This closes the denominator. The earlier architecture jumped from population commitment to successful linkage, which left every unlinked eligible case outside the status machinery: a thousand committed cases could become nine hundred and twenty analyzed ones with nothing in the record. The verifier now requires a track for every membership-committed case and rejects a package missing one.

Subsequent events: `outcome_observed`, `adjudicator_assessment_committed`, `reference_standard_adjudicated`, `linkage_status_updated`, `outcome_integrity_event`.

---

### 6.12 Resolution and uniqueness (normative)

Every artifact reference in a package resolves through one rule: a reference resolves only if exactly one shipped artifact matches its identifier and version, and that artifact's content hash recomputes to the referenced digest. This applies uniformly to definition artifacts, derived artifacts, criteria cited by adjudications, definition versions cited by snapshots, and dependencies cited by derived artifacts.

Within one package, every logical identifier MUST resolve unambiguously according to the identifier-specific uniqueness rules in `CLAIMS-CLASSIFICATION.md`. <!-- req:4.1 req:3.6g req:3.1j req:3.1d req:5.1b --> Unique: artifact identifier plus version, key reference, chain reference, event identifier within a chain, membership leaf under `unique_decision_instance`, and derived artifact identifier. Ambiguity is a conformance error, never an implementation choice.

### 6.13 Primary-criterion status accounting

OL requires a replayable status under the primary evaluation criterion for every linked case; the verifier reports this as an explicit profile requirement. <!-- req:6.13 -->

### 6.14 Mature linked cases are adjudicated

OL requires every mature linked case to have one active adjudication under the primary criterion; the verifier derives the active leaf from adjudication lineage rather than physical event order. <!-- req:6.14 -->

## 7. Derived artifacts

### 7.1 No mutable state

Derived artifacts carry no lifecycle field. Effective status is replayed from `derived_artifact_registered`, `derived_artifact_superseded`, and `derived_artifact_invalidated` events. An immutable object cannot have a field that changes later, and the previous draft's `status: active` field was exactly that contradiction.

### 7.2 Recomputability at scale

Inline input hashes up to a declared threshold; above it, an input-set commitment with an RFC 9162 manifest root. Recomputability is deterministic recomputation under the declared canonicalization and software digest, against the referenced snapshot, over the committed input set.

### 7.3 Assurance

Single-subject artifacts carry an assurance vector; aggregates carry inclusion filters, never a single vector. Rewrite detection is not among the stored fields: it is derived per chain by the verifier and reported as a coverage map (Section 3.7), because a stored grade would be false for exactly the newest evidence.

### 7.4 Snapshots ship their tuples and recomputation is frozen

An analysis snapshot carries its population tuples inline, so the committed root is recomputable and each tuple's head is bound to the actual chain event at that sequence. Metric recomputation then TRUNCATES every case chain to its snapshot sequence before replaying adjudication state, so a superseded v1 artifact verifies against the evidence that existed when it was derived, not against the live export. Later evidence must not rewrite what the analytic dataset was; a verifier that recomputes against the latest state cannot distinguish an honest historical metric from a fabricated one that happens to match today. The committed `input_event_hashes` are then compared against the adjudication events the recomputation actually used, collapsing "these were my inputs" and "this is the recomputed number" into one story.

### 7.5 Store evidence, derive assurance

A derived artifact carries a reference to its governing analysis plan, not a conclusion about that plan's prespecification. The verifier follows metric to snapshot to plan to plan hash to anchor receipt to cutoff comparison and derives the grade. A disclosure that simply wrote `externally_anchored` would look authoritative while establishing nothing, which is the failure mode the entire specification is organized against.

### 7.6 Superseded is not invalidated

A metric correctly computed against an earlier snapshot remains a correct historical computation when evidence advances; it is superseded. Invalidation is reserved for computations that were non-conformant or erroneous. Preserving that distinction is one of the architecture's strengths, and collapsing it would punish honest longitudinal work. When an adjudication is revised, dependent artifacts MUST be superseded (or invalidated where the earlier computation was itself defective), <!-- req:7.1c --> and the verifier rejects an active artifact depending on a superseded adjudication.

---

## 8. Metrics

### 8.1 Commensurability

RAIR, RSR, SRF, and EAR require that baseline, AI output, and evaluation state be evaluable against the same criterion, target time, and compatible answer space, or a declared validated mapping. DIRECTIVE and AGENTIC exposures are frequently ineligible; exclusions are counted and disclosed.

### 8.2 Binary validity, and the corrected definitions

The identity SRF = 1 − RSR holds only when validity partitions into correct and incorrect within the denominator. `partially_correct` and `not_classifiable` therefore MUST be excluded via the criterion's declared binary projection, and the exclusion counts disclosed. <!-- req:8.2 --> With E as the projection rule's evaluation state:

- **RAIR** = P(E correct | baseline incorrect, AI correct)
- **RSR** = P(E correct | baseline correct, AI incorrect); **SRF** = 1 − RSR
- **EAR** = P(E **incorrect** AND E aligns with the AI under the metric definition's declared alignment relation | baseline correct, AI incorrect). The conjunction is required: movement toward an incorrect AI that stays within tolerance is not error adoption, and without it EAR is not bounded by SRF.

  **The alignment relation is declared, not implied.** A metric definition whose `metric_name` is `EAR` MUST carry an `alignment_relation` executable <!-- req:8.9 -->, with an identifier, a code artifact, a digest, and fixtures, exactly as Section 4 requires of projection rules and estimators. Until rc4 this specification said "same-or-toward" in prose while the reference implementation compared for equality, and nothing in the package declared which was meant. Alignment is owned by the **metric definition**, not by the criterion, because two metrics may legitimately operationalize alignment differently against the same reference standard. For `alignment-same-v1`, alignment means exact agreement with the AI output; it declares itself valid only for `nominal` answer spaces, and the verifier enforces that against the criterion's declared `answer_space_semantics` <!-- req:8.9 -->. Ordered, interval, or continuous answer spaces require another declared relation, since "toward" presupposes an order a nominal space does not carry.

### 8.3 Evaluation state and actor

`evaluation_state` is `proximal_post_exposure`, `final`, or a declared alternative; proximal response and final decision are different estimands and the formulas reference the declared one. Self-reliance requires `baseline_actor == evaluation_actor`; multi-actor trajectories are team-reliance constructs.

### 8.4 WOA (informative in v0.2.0-rc8)

WOA remains a supported descriptive construct but is not part of OL conformance in this release candidate and is not recomputed by the reference verifier. Deployments that report it should preserve the raw distribution, label bounded variants, and count equal-advice exclusions. WOA near zero against correct advice and negative WOA represent different behaviors and should be reported separately.

### 8.5 Disclosures

Completeness accounting across the full committed population including linkage failures, the stable verification-rule identifier (`OL-ADJUDICATED`), blinding-record breakdown, primary-criterion identity and validation presence, commensurability exclusions, binary-projection exclusions, and a reference to the governing analysis plan. Every required field is recomputed from snapshot-frozen evidence or pinned definition artifacts. `blinded_committed` describes what the committed record establishes; actual adjudicator blinding remains the A-class requirement 6.11e.

### 8.6 What recomputation currently establishes

The reference verifier recomputes RAIR, RSR, SRF, and EAR from the resolved v0.1 trajectories, the adjudicated conclusions, the projection rule's eligibility, and the criterion's binary projection, and compares the result to the registered artifact, including exclusion counts. This is semantic recomputation, not merely arithmetic consistency. It executes the declared rule modules against snapshot-frozen evidence through the same orchestration engine the generator used, whose digest is bound and recomputed on every run. What this establishes is that the declared rules, applied to the committed evidence, reproduce the registered counts. What it does not establish is agreement between two independently written implementations: the shared surface is the whole orchestration function and the canonicalization primitives, not merely low-level helpers. Independent recomputation is therefore classified `not_implemented` rather than described as achieved, and is the single most valuable contribution an outside implementer could make to this specification.

### 8.7 Interval reporting and recomputation

When a metric definition declares an interval method and the denominator is nonzero, the derived metric artifact MUST carry that interval and the verifier MUST recompute it under the declared estimator before accepting the artifact. <!-- req:8.7 --> This requirement concerns faithful execution of the declared uncertainty procedure; whether that procedure is substantively appropriate for the external-world estimand remains outside conformance verification (Section 8.8).

### 8.8 Statistical characterization is out of scope for conformance verification

DSES can establish that an estimate was computed as declared from committed evidence. It does not mechanically establish that the chosen estimand, sample, model, or uncertainty procedure adequately characterizes the external world; those questions remain statistically assessable and, in part, judgment-dependent. <!-- req:8.8 -->


---

## 9. Privacy, retention, governance

The chain commits to payload commitments, so deletion under legal policy never breaks chain verification, and hiding commitments make destroyed low-entropy content non-enumerable from the commitment. v0.1 Section 10 applies in full. Core objects are closed, so a privilege-determination field is schema-invalid rather than merely discouraged.


### 9.3 Unit of analysis, longitudinal secondary use, and adverse-action boundaries

DSES records, for every eligible decision, whether a professional formed a judgment and then did or did not adopt an AI output. Aggregated over months or years, those records can become a performance-surveillance dataset. That consequence is not neutral merely because the protocol itself does not make employment, credentialing, or legal decisions. The evidence model determines what can later be reconstructed, so this specification constrains the derivations it will call conformant.

**Unit of analysis is prespecified.** Every cohort MUST declare a `unit_of_analysis` <!-- req:9.3a -->, anchored before enrollment like every other definition. A derived metric MUST NOT be reported at a finer unit than the cohort authorises <!-- req:9.3b -->. A cohort assembled to evaluate a system and later re-cut per clinician is a different analysis from the one that was prespecified.

**Individual metrics are actually individual.** An `individual_clinician` metric MUST bind a `subject_ref`, and every committed input to that metric MUST arise from a decision sequence whose baseline and evaluation actor are that subject <!-- req:9.3g -->. The reference verifier filters the snapshot-frozen evidence by actor before recomputation; changing only the label on a cohort metric is therefore a conformance failure. An individual metric MUST also declare an `observation_window`, and that window MUST fall within the maximum longitudinal window authorized by its governance artifact <!-- req:9.3h -->. A career-to-date accumulation is not implicit permission to use an entire career.

**Individual-level derivation requires governance.** An `individual_clinician` metric MUST resolve a `secondary_use_governance` artifact <!-- req:9.3c -->, itself prespecified and externally anchored. The artifact declares a structured purpose, the maximum decision consequence the analysis is authorized to inform, authorized recipients, the review body, the maximum observation window, minimum cell size, case-mix requirements, subject notification, appeal pathway, retention, and high-stakes safeguards. Quality improvement, research, credentialing, employment action, litigation support, and regulatory oversight are not interchangeable purposes.

**High-stakes use cannot be encoded as aggregate-only discipline.** For `credentialing`, `employment`, `litigation_support`, or `regulatory_oversight`, the governance artifact MUST state that an aggregate DSES metric is not a sufficient sole basis for adverse action, MUST require case-level review, MUST require subject notification and access to the evidence used, and MUST provide an appeal mechanism <!-- req:9.3j -->. DSES can mechanically establish that those safeguards were declared before the analysis. It cannot establish that a hospital, employer, court, insurer, or licensing body actually honored them; actual downstream compliance remains external to DSES. <!-- req:9.4b -->

**The context population is the assigned population.** An individual metric MUST bind a prospective `responsibility_assignments` artifact, anchored before enrollment, that attributes decision instances to professionals independently of later linkage <!-- req:9.3n -->. Its `reliance_context` MUST cover every assigned instance in the window, with linkage, maturation, and adjudication breakdowns that reconcile exactly to the instance count, and the metric-eligible subset MUST be derivable from that population <!-- req:9.3l --> <!-- req:9.3m -->. Cohort denominator closure does not confer clinician denominator closure: without prospective assignment, a subject's failed linkages vanish from the subject's own record, and an adjudication breakdown computed over adjudicated cases cannot show non-adjudication. Governance MUST declare whether it was prospective or retrospective to the observations, checked against its own anchor <!-- req:9.3o -->; prespecified relative to an analysis cutoff is not prospective authorization of surveillance. Case-mix disclosure is established mechanically; adequacy of an adjustment, and any risk-adjusted claim, are not <!-- req:9.3p -->. Pseudonymous subject binding does not establish civil identity <!-- req:9.3r -->.

**Small denominators, case mix, and context travel with the rate.** An individual-level metric MUST meet the governance minimum cell size and MUST ship its interval <!-- req:9.3d -->. It MUST disclose the case-mix covariates and whether an adjustment was performed <!-- req:9.3e -->. DSES does not claim that the adjustment is statistically adequate; adequacy of a case-mix model is a statistical and domain judgment, not a schema fact. <!-- req:9.5 -->

An individual-level metric also MUST carry a verifier-recomputed `reliance_context` over every subject case in the bounded observation window, not merely the denominator of the rate being displayed <!-- req:9.3i -->. The context includes adjudication-status and commensurability breakdowns, baseline/AI/evaluation validity breakdowns, the AI-system mix, and exposure-class mix. This is intentionally broader than RAIR, RSR, or EAR alone: a conditioned rate cannot be detached from how often the AI was right or wrong, what kind of outputs were shown, or what fraction of the subject's cases were even evaluable.

**A worked individual derivation ships with this specification.** `examples/derived/derived-rair-subject-0417-v1.json` is a subject-scoped metric for one reader over a 121-day window under a quality-improvement governance artifact, with its interval, its case-mix disclosure, and its verifier-recomputed reliance context. It is included because the governance rules were previously exercised only by adversarial fixtures, and a section addressed to review bodies and counsel needs something they can read. `RELIANCE-CONTEXT-EXAMPLE.md` renders it as a committee would receive it.

**What the metrics are not.** A DSES artifact or DSES conformance claim MUST NOT assert that a metric establishes a standard of care, reasonable AI use, professional competence, negligence, legal authority to take action, admissibility, or an employment/credentialing action recommendation <!-- req:9.3f -->. DSES also does not determine whether a record is discoverable, privileged, legally usable, or sufficient under any jurisdiction's professional-liability or employment law; those are external legal questions, not protocol outputs. <!-- req:9.3k -->

### 9.4 Declared purpose is not downstream control

DSES records the declared purpose and authorized recipients of an individual-level analysis, but it cannot technically prevent a recipient from copying a number into another process. That a metric is actually used only for its declared purpose by its authorized recipients is therefore an A-class requirement, not a property the verifier can establish. <!-- req:9.4 --> The same is true of whether a review body performs the case-level review, access, notice, and appeal procedure it declared. <!-- req:9.4b -->

### 9.5 No bounded definition of "reasonable AI use"

DSES does not define a Bayesian band, percentile, override rate, or other numerical threshold as "reasonable" or "unreasonable" AI reliance. Such a threshold would require an empirical reference population, a stable task definition, comparable AI versions, case-mix handling, an estimator, and an external normative decision about what consequences the distribution should carry. DSES supplies evidence needed to estimate those distributions; it does not convert a distribution into a professional norm.

The reliance metrics are conditioned, not raw adoption rates. RSR concerns cases in which the baseline human judgment was correct and the AI was incorrect; SRF therefore describes abandonment of a correct judgment for an incorrect AI output. RAIR concerns the converse opportunity for a correct AI output to rescue an incorrect baseline. An individual `reliance_context` makes those opportunities and the underlying AI-error exposure visible alongside any rate. This is the appropriate evidentiary foundation for future empirical reference-range research, but a reference range remains descriptive unless an external authority separately adopts a normative policy.

How well a case-mix model, empirical reference distribution, or Bayesian/hierarchical model characterizes real professional practice remains statistically assessable and judgment-dependent rather than mechanically decidable by DSES. <!-- req:9.5 -->

---

## 10. Conformance verification

Conformance has two mandatory layers: **schema validation** and the **DSES semantic-cryptographic verifier**. Per v0.1 Section 12, an I2-or-above claimant MUST make a verifier and sample export available. <!-- req:10.2 -->

This package ships both. `scripts/dses_verify.py` performs the C and X checks enumerated in `CLAIMS-CLASSIFICATION.md` and prints its attestation list on every run. `tests/run_regression.py` contains the adversarial suite, and every verifier fixture asserts the SPECIFIC rule that must fire. Fixtures rebuild orthogonal cryptographic layers when practical; cascading failures are permitted, and a fixture earns only the claim that its named rule fired. The suite is drawn from successive external-review rounds; `run_all.sh` is the CI gate. Where this document says the verifier establishes something, a check and a fixture exist for it. Where it does not, the requirement is classified A and stated as an attestation.

---

## 11. Schema discipline

**No conformant calculation or conformance claim may depend on an extension unless that extension is explicitly incorporated by a versioned normative definition artifact.** Schema isolation alone cannot prevent an extension from altering downstream semantics, so the constraint is stated as a requirement on calculations rather than on syntax. Core objects closed with `unevaluatedProperties: false` and a single namespaced `extensions` object; `event_type` bound to payload by discriminated union; integrity classes conditionally requiring their evidence and logically admissible on their face (an I3 claim requires at least one defining capability true, while truth of the evidence is the verifier's job); temporal fields constrained by calendar-aware patterns, with instant validity itself classified X because a regex cannot decide it; URIs pattern-constrained for the same reason; integers bounded to the JCS-safe range. Schema `$id`s are `/0.2.0-rc8/` in this candidate. The permanent `/0.2.0/` identifiers are minted once, when public comment closes, and never reused, which is why this build is a release candidate rather than the release: an identifier that cannot be withdrawn should not be spent on a document still under review.

---

## 12. Conformance claims and the OL profile

Profile conformance is evaluated explicitly, not inferred from the absence of failures. The verifier also prints two distinct lists that earlier drafts conflated: the **normative attestation inventory**, generated directly from the A-class rows of `CLAIMS-CLASSIFICATION.md`, and the **limitations of that particular invocation** (no witness supplied, RFC 3161 profiles not credited, shared recomputation primitives). A conformance claim may never assert a requirement from the first list; the second list describes what this run did not attempt. The verifier ends with a `PROFILE` block reporting each OL requirement individually and a single verdict, because passing every cryptographic check is not the same as satisfying a profile.

> "DSES 0.2 at L2 / originating v0.1 integrity class declared I2 + OL: membership-committed periodic manifests, append-only checkpoint log anchored under DSES-ANCHOR-v1 against an external trust root, definitions externally anchored before the declared enrollment cutoff, committed-assessment adjudication with recomputed agreement; verifier and sample export available; attested requirements enumerated per CLAIMS-CLASSIFICATION and printed by the verifier."

**OL requires:** membership-committed manifests; a track for every committed member with terminal linkage accounting; a declared cohort with one primary criterion and a precommitted analysis plan whose prespecification assurance and cutoff are stated; linkage security and accuracy groups; per-criterion maturation and status accounting; an adjudication conclusion status for every mature linked case under the primary criterion; packet-manifest blinding provenance; a snapshot for every published metric; Section 8.5 disclosures; and a passing verifier run. **OL-declared** is the weaker variant for count-only manifests or declared-only prespecification.

---

## 13. What this layer does not claim

No causal claim. No completeness claim at any assurance level. No historical-immutability claim absent a named trust anchor. No claim that adjudication yields truth. No claim that a criterion is the right criterion.

---

## Annex A (informative): Regulatory context

DSES is an evidence-representation specification, not a regulatory-compliance determination. The regulatory context described in v0.1 carries forward without changing the conformance machinery in this layer. The FDA guidance cited in that context is described as originally issued December 4, 2024 and reissued August 18, 2025.

## Annex B (informative): Worked example

`examples/example-package.json` contains twelve membership-committed eligible cases, each with a case track. Ten link to a resolvable, replayable DSES v0.1 decision sequence shipped in `examples/decision-sequences/`; one fails linkage because no instrumented decision record exists; one links but remains immature. The population exercises every arm of the reliance metrics: RAIR numerator and denominator-only cases, an RSR success, a self-reliance failure that adopts the AI's error, a self-reliance failure that does not, a partially correct evaluation excluded by the binary projection, a noncommensurable DIRECTIVE exposure, and an indeterminate adjudication. An adjudication is then revised, which supersedes the first metric set and produces a second; RAIR moves from 1/2 to 1/3 and RSR from 1/2 to 0/1 as a result.

Every cryptographic artifact is real: RFC 8785 preimages, RFC 9162 inclusion and consistency proofs over an append-only head-observation log, ed25519 signatures under DSES-SIG-v1, verifiable anchor receipts, and randomized hiding commitments. `bash run_all.sh` regenerates and reverifies everything from a declared dependency manifest, and ends with an explicit OL profile verdict.

## Annex C: Changelog

**0.2.0-rc8.** Governance proof-boundary release, scoped to the four gaps an independent deep review found between what Section 9.3 claims and what the verifier establishes, and deliberately nothing else. The context population is repaired: an individual metric now binds a prospective responsibility-assignments artifact independent of linkage, its reliance context covers every assigned instance in the window with linkage, maturation, and adjudication breakdowns that reconcile exactly to the instance count, and the metric-eligible subset is derivable from that population. Before this, the context was computed over metric-eligible cases and then filtered to the subject, so a subject's failed linkages vanished from their own record and the adjudication breakdown could not show non-adjudication, defeating its anti-cherry-picking purpose; the shipped example was numerically correct only because its subject happened to own no failed linkages, and it now owns two non-eligible instances precisely so the repair is visible. Governance must declare prospective or retrospective timing, checked against its own anchor. Window arithmetic is exact seconds, not truncated days. Case mix is narrowed to what is established: disclosure is mechanical, adequacy and risk-adjusted claims are not. Privacy basis and professional identity mode are declared, with validity of the legal basis external, and pseudonymous binding is stated not to establish civil identity. Four fixtures, seven claim rows. The suite stands at 145; checks at 2,236.

**0.2.0-rc7.** Ships the individual derivation the governance layer describes. rc6 added subject scoping, bounded windows, balanced context, and high-stakes safeguards, but the worked example remained cohort-level, so those rules executed only against adversarial fixtures and the check count did not move. Building the example exposed a defect in the feature the pass was named for: the balanced context builder tested the binary validity projection against `True` and `False`, while the projection returns the validity string, so every case fell through to `excluded` and the AI-error and baseline-correctness breakdowns were uniformly zero. Both sides of the check computed the same degenerate answer, so the adversarial fixture agreed with it. The builder is fixed, two fixtures now reject a context reporting every case excluded and one understating AI error, one reader owns a slice of the cohort so an individual derivation has a denominator, and the shipped package carries a governance artifact and a subject-scoped metric. Verifier checks move from 2,140 to 2,210, which is the signal that the governance layer is now exercised by the package rather than only by attacks. The suite stands at 141.

**0.2.0-rc6.** Longitudinal-governance pass after external clinical-liability review. Individual-level metrics are now genuine subject-scoped derivations: the verifier filters snapshot-frozen trajectories by `subject_ref`, checks every committed input belongs to that subject, and applies a declared bounded observation window. `secondary_use_governance` gained structured purpose and decision-consequence fields, a maximum observation window, and mandatory high-stakes safeguards. Credentialing, employment, litigation-support, and regulatory uses must predeclare that aggregate metrics are not a sufficient sole basis for adverse action, require case-level review, provide subject notice and access to the evidence, and provide appeal. Every individual metric now carries a verifier-recomputed balanced reliance context covering the full bounded subject window: adjudication status, commensurability, baseline/AI/evaluation validity, AI-system mix, and exposure-class mix. The specification explicitly separates case-mix disclosure from statistical adequacy, and separates DSES evidence from legal authority, admissibility, discoverability, privilege, standard of care, competence, negligence, and adverse-action decisions. No numerical band is labeled "reasonable AI use"; DSES supplies evidence for future empirical reference distributions without turning a distribution into a norm.

**0.2.0-rc5.** Governance layer, added after an external clinical critique that the specification had built a per-clinician surveillance instrument and said nothing about its use. The critique was correct: nothing constrained unit of analysis, so a cohort assembled to evaluate an AI system could be re-cut per clinician and handed to a credentialing committee, and the architecture made that trivial. Section 9.3 is the answer. Cohorts declare a prespecified, anchored unit of analysis; no metric may be reported at a finer unit than the cohort authorises; individual-level derivation requires an anchored `secondary_use_governance` artifact naming purpose, authorised recipients, review body, minimum cell size, case-mix requirement, subject notification, appeal pathway, and retention; individual-level metrics must meet the minimum cell size, ship their interval, and disclose case mix; and no artifact may assert a standard-of-care, reasonable-use, or competence determination. Nine new adversarial cases, including the per-clinician recut itself. Section 9.3 also states plainly what DSES cannot do: it supplies no bounded definition of reasonable AI reliance, because no distribution of reliance behaviour has been measured to define one against, and a threshold asserted before that measurement would be a number invented to look like evidence. What it records instead are conditioned quantities, whose denominators are the cases where the AI was wrong, so the same record that appears to expose a clinician who resists AI documents the occasions when that resistance was correct. The suite stands at 135.

**0.2.0-rc4.** Repair-defect pass. The second implementation reported that five defects were introduced by rc3's own repairs, and four of them were the same pattern: rc3 diagnosed that a digest without a locator answers what to hash but not from where, then placed answer-space requirements, interval methods, confidence levels, tolerances, and quantile constants in Python module constants with no data field, so a second implementation had to transcribe them from the reference realization. Executable references now carry `parameters` as data, the module must agree with them, and `RULE-PARAMS` checks that agreement. The duplicated digest field is gone: `code_artifact.digest` is the only one. The derivation engine, the single digest rc3 did not fix, now carries a locator too.

The finding worth acting on first was different in kind. Every charter constraint was reached THROUGH the cited assessments, so an adjudication citing none escaped all of them, and the worked example's own revision, the one that moves RAIR from 1/2 to 1/3, did exactly that: zero assessments, a resolution method no charter field authorized, and an agreement value the declared statistic returns nothing for. rc3's headline repair was defeated on the most consequential adjudication in its own example, one door over from the laundering path Section 6.10 closes. Adjudications now bind their charter directly, charters declare a revision protocol naming authorized methods and which may proceed without new assessments, an assessment-free resolution must name a decider holding the authorized role, and it must assert no agreement statistic.

Also closed: the interval tolerance, stated four times in three documents and contradicting itself twice, is now declared once as data and is absolute; requirement 3.2d's reclassification reached the claims row and class letter, not only the prose; and release lint gained a manifest-freshness check after the in-repo `RELEASE-MANIFEST.sha256` was found describing rc2 while the archive's regenerated copy verified clean, one artifact with two truths. The suite stands at 126.

**0.2.0-rc3.** Specification-completeness and interoperability pass, driven by an independent implementation attempt and a follow-on audit of the repair. The repair audit found the same failure mode the repair was meant to remove: the agreement statistic was declared as an executable rule, digested, and fixtured, while the verifier went on computing agreement inline by comparing every assessment against the first one. Those are different algorithms as soon as a third reader exists, and the inline one made assessment-reference ORDER change the answer, in a document whose Section 6.10 says physical order is never truth. Adjudication now calls the charter's declared rule. Four further single-source-of-truth defects were closed: independent assessments must now come from distinct adjudicators rather than merely numbering two, a declared `interval_method` must equal its declared estimator's method, a stale `alignment_relation_spec` field that no one used was deleted rather than deprecated inside an unreleased candidate, and executable references now carry an explicit media type and locator, because a digest without a locator answers what hash but not of which object and left a second implementation reverse-engineering a path convention private to this one. The nonce sidecar is schema'd and keyed by event hash, since event identifiers are unique only within a chain. Requirement 3.2d no longer claims to depend on the external trust root, which it never did. The claim that fixtures are the conformance surface was overstated and is now correct: declared semantics are normative, the module is a reference realization, and fixtures are mandatory interoperability vectors, because a finite vector set cannot uniquely determine a program. Release lint gained uniqueness of requirement identifiers, which immediately found `3.8a` denoting two different requirements and silently corrupting the generated counts, and a stale-version check, which found the citation block still naming rc2. The original pass, driven by the first attempt to implement this document without access to the reference implementation. That attempt reached OL CONFORMANT, which is meaningful, but it did so only after recovering by experiment things the prose never said, and those recoveries are the findings. The DSES-SIG-v1 signed statement was underspecified: the layout was given, the length encoding and the hex-versus-raw question were not, and the implementer enumerated ninety-six candidate encodings against a known-good receipt to find the one that verifies. Section 3.6 now specifies the encoding normatively, tabulates what every one of the seven contexts commits to (five were listed before, and what each target covered was stated for none), and the package ships `fixtures/dses-sig-v1.testvectors.json` with a published seed, exact signing-input bytes, and valid signatures, which the verifier self-tests before examining any package. The alignment relation EAR depends on did not exist as a declared artifact: Section 4 requires alignment relations to carry an identifier, a digest, and fixtures, and this package computed alignment as an inline equality while the prose said "same-or-toward", two different relations. `alignment-same-v1` is now declared, digested, fixtured, and used by both engines, and Section 8.2 records why the twelve-case example cannot distinguish the two readings and where they actually diverge. The estimator module content-addressed for the interval did not compute the interval; it now does, with published quantile constants, a normative association order, and a stated absolute tolerance of 1e-9, because demanding bit equality across languages would make an independent implementation impossible while sounding stricter. Percent agreement over non-assessable assessments was undecided in prose and is now an executable charter rule: two adjudicators who agree the evidence is insufficient have agreed. Nonce transport is documented and requirement 3.2d reclassified: it needs the package, the trust root, and the nonce sidecar, three inputs, not two. Section 3.8 no longer requires a verifier to execute shipped Python, which had made it mutually exclusive with requirement 7.3c; a verifier must recompute code digests and conform to shipped fixtures, and may implement the declared semantics natively. Rule ownership is settled where several checks could fire, so two conformant verifiers cannot disagree about what a package did wrong. Three fixtures were added and the suite stands at 117.

**0.2.0-rc2.** Publication-readiness pass after the eighth review round. Signature-profile validation now covers profile, algorithm, context, target, key status, and every optional event signature; external anchor trust must be supplied explicitly; disclosure recomputation is snapshot-frozen and covers every required field; the derivation digest now binds the actual shared orchestration module; nonce length is checked while randomness quality is explicitly attested; normative traceability tags and release lint were strengthened; WOA and current payload-disposition replay are no longer overclaimed. The prior verification-contract work remains: The headline finding was that the specification had become more rigorous than its own test suite: `CLAIMS-CLASSIFICATION` defines "implemented" as a check plus a fixture asserting that check's rule, and twenty-five implemented rows named rules no fixture exercised. Fifty-seven targeted verifier fixtures were added in that pass; subsequent publication-readiness cases expanded the suite further, with every verifier fixture asserting the specific rule that rejects it. `scripts/release_lint.py` now enforces that definition mechanically, fails the build when an implemented rule lacks a fixture, when the verifier emits a rule the claims table does not document, or when a normative requirement is unclassified, and regenerates the claim counts so no inventory number is typed by hand; three mutually inconsistent count statements existed before it. Two tautological checks were found and removed rather than left as decorative assurance. The verifier now yields a verdict rather than a stack trace on structurally unprocessable packages, prints the normative attestation inventory generated from the claims table separately from the limitations of the invocation, and requires a criterion status under the primary criterion for every linked case. Sections 3, 6, 7, and 8 were renumbered into a single ascending sequence and every companion reference repaired; Section 4 and Section 10 requirements that had no claims rows were added. The release gate was inverted: shipped artifacts are linted, validated, verified, and attacked BEFORE anything is regenerated, and regeneration writes to a temporary tree, because generating first proved only that the generator can produce a passing package. Scoped CC BY 4.0 and MIT license files ship; build artifacts and merge notes do not. The publication builder now uses an explicit allowlist and emits a SHA-256 release manifest, so archive hygiene is a build property rather than a manual cleanup step.

**0.2.0 (superseded by rc1).** Proof-layer release after the sixth review round, which demonstrated that the previous build could return a conformant verdict over materially altered evidence. The anchor trust root moved outside the package: receipts verify only against a reader-supplied trust store, and the full A1 attack (genesis key substituted, receipts re-minted, history rebuilt) is a regression fixture asserted to die at the receipt rule. v0.1 payload commitments are verified for every consumed event, so the reviewer's demonstrated tamper (an independence class flipped in a bound sequence, nothing else touched) dies at the commitment rule with surgical precision. Executable rules became actual code: digests are recomputed from module bytes, shipped fixtures are executed against the loaded modules, and metric recomputation runs the declared rules rather than a parallel implementation, with the derivation software digest bound to the real engine bytes. Snapshots ship their population tuples; roots are recomputed; recomputation is performed against snapshot-truncated chains, so superseded metrics verify against their frozen evidence; committed input sets are compared to the inputs actually used. Adjudication lineage is a verified DAG with laundered and forked revisions rejected; charter roster, assessment minimums, resolution methods, and inter-adjudicator agreement are enforced or recomputed; maturation is derived from index date, risk window, and cutoff; manifest latency and checkpoint cadence are checked against declared policy. Periodic manifests are first-class, with tracks bound to their manifest by event hash and denominators aggregated across manifests. Every semantically consequential definition reference is pinned (identifier, version, content hash); genesis commits the definition set and snapshots must equal the reconstructed in-force set. Derived artifacts lost their stored prespecification label, gained mandatory Wilson intervals over nonzero denominators, and every disclosure field is recomputed by the verifier from its own replay. The regression suite was expanded with targeted rule-asserting fixtures. Remaining not-implemented items are named in CLAIMS-CLASSIFICATION: RFC 3161 token parsing, and recomputation by a fully independent engine.

**0.2.0-draft.4.** Verification-boundary pass after the fifth review round: referenced v0.1 decision sequences now resolve, replay, and are checked for baseline-exposure-evaluation ordering and actor identity; keys resolve only from the hash-chained genesis directory, with rotation, revocation, validity windows, and uniqueness enforced; external anchoring is derived from cryptographically verifiable receipts (DSES-ANCHOR-v1) rather than asserted, with anchor distrust event-sourced and RFC 3161 parsing declared not implemented; rewrite detection is a per-chain coverage map rather than a package badge; a single resolver rule covers every artifact reference, with package-wide uniqueness constraints; membership leaf uniqueness closes the duplicate-denominator hole; checkpoint coverage is measured against a declared policy and reported separately from log integrity; track state is replayed rather than asserted alongside attempt results; derived artifacts resolve generically and store plan references rather than prespecification conclusions; RAIR, RSR, SRF, and EAR are recomputed from first principles and compared to registered values; profile conformance is evaluated and reported explicitly; the claims table gained a reference-verifier-support dimension separate from verification class; the worked example grew to twelve cases exercising every metric arm, an adjudication revision, and metric supersession.

**0.2.0-draft.3.** Protocol normalization after external review of draft.2: append-only checkpoint log replacing the mathematically impossible consistency claim over mutable current heads, with head observations carried for offline recomputation and bound to exported chains; anchors moved outside the objects they attest; DSES-SIG-v1 signature profile with domain separation, committed key directory, and named contexts; case tracks for every committed population member, closing the linkage-failure denominator hole; membership leaf carried in the track genesis so inclusion proofs are self-contained; derived lifecycle moved to events with superseded distinguished from invalidated; adjudication revision as a first-class event rather than a nested payload; snapshot binding cases to heads in one tuple tree and committing the preceding cohort head; generic `evaluation_criterion` implemented in the schema with clinical, policy, and benchmark specializations; prespecification judged against declared external cutoffs rather than ingestion order; `initial_payload_disposition` with replay-derived current status; nonce terminology, transport, and a precisely stated hiding-commitment security claim; hiding enforced by schema for low-entropy event types; single hash-agility story; JCS-safe integer bounds and calendar-aware temporal patterns; capability flags renamed to `internal_chain_consistency` with `historical_rewrite_detection` as a separate derived property; method-specific linkage security descriptors; binary validity projection required for the reliance metrics; explicit threat model A1 through A7; `CLAIMS-CLASSIFICATION.md` and the thirty-case adversarial suite shipped rather than promised; dependency manifest and one-command reproduction.

## Annex D (normative): Claim classification

Every normative requirement using an uppercase conformance keyword carries a stable requirement tag and two independent labels in `CLAIMS-CLASSIFICATION.md`, which is release-blocking and ships with this release candidate. **Verification class** (S, C, X, T, A) answers what kind of establishment is possible in principle. **Reference verifier support** (implemented, partial, not_implemented) answers whether this build performs it. Conflating the two would let an unimplemented check hide inside an optimistic classification. Current counts: 31 S, 30 C, 85 X, 2 T, 20 A; 120 implemented, 2 partial, 3 not implemented.

---

**Citing this specification:**

> Henderson JM. Decision-Sequence Evidence Schema, version 0.2.0-rc3: the outcome-evidence layer. Evidify LLC; 2026. Release candidate for public comment.

**Review provenance and AI disclosure.** This release candidate was shaped by eleven rounds of detailed adversarial technical review conducted by an AI system <!-- REVIEW-SYSTEM-UNSPECIFIED -->, and its reference implementation was written by an AI system. No human subject-matter expert has yet reviewed this specification or its implementation. This is disclosed rather than acknowledged: attribution implies accountability for the claims made here, an AI system cannot hold that accountability, and the author retains full responsibility for every claim in this document, including those the machine review failed to catch. Readers should weight this accordingly. The compensating design choice is that this specification's claims are constructed to be machine-checked rather than vouched for: every requirement marked implemented names a verifier rule and a regression fixture that asserts that rule fires, `scripts/release_lint.py` fails the build when that correspondence breaks, and a reader may re-run the entire gate rather than trust any reviewer, human or otherwise. That substitutes verifiability for authority; it does not substitute for expert review, which remains outstanding and is named as such. One episode is worth recording for calibration: in the eighth round the reviewing system reported a canonicalization defect in two derived artifacts that did not exist, having used a non-conforming JSON canonicalizer in an environment that could not install the pinned dependency. The finding was wrong; the fail-fast canonicalization self-test it prompted was kept, because the failure mode it guards against is real. Machine review is useful and it is not self-validating.
