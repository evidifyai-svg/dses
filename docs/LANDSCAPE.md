# Landscape: adjacent specifications and how the DSES core relates to them

Status: working document. Outside the release allowlist, so it never changes an archive digest. First entry 2026-09-03.

## Rules for every entry

1. Every statement about another specification is traceable to that specification's public text, with the URL and the date it was read. Nothing is inferred about a mechanism the public text does not describe. Where the text is silent, the entry says "not stated on the pages read", never "does not exist".
2. Every statement about the Decision-Sequence Evidence Schema (DSES™) is no stronger than the strongest claim the published DSES specification makes about itself, and cites the section.
3. Relationships are expressed with the vocabulary the companion namespace policy uses for adoption mappings: `identical`, `narrower-than`, `broader-than`, `superseded-by`, plus `no-counterpart` where one side has nothing to map to. The direction is always the other specification's concept relative to the DSES concept.
4. No entry describes the DSES core as an implementation, profile, layer, or subset of another specification. Where an interoperability path exists it is described as an application profile of the DSES core emitting into the other specification's container, and it is described once.
5. These rules migrate into `CLAIM-LEDGER.md` as its comparison-language section when that file lands (rc12 scope).

---

## 1. Veriscopic Evidence Standard (VES) v1.1

**Steward:** Veriscopic (veriscopic.com).
**Text read:** https://www.vesstandard.org/ (framework page), https://www.vesstandard.org/specification (normative text, v1.1, ten sections), https://www.vesstandard.org/certification, https://www.vesstandard.org/stewardship. All read 2026-09-03. Trade-press context: Insurance-Edge.Net, 2026-08-24 and 2026-09-01, by Drew Young, founder of Veriscopic.
**Domain as stated:** consequential human, organisational, or system-assisted judgement subject to audit, dispute, or regulatory scrutiny; product pages name insurance claims, underwriting, parametric triggers, and consent evidence.
**Insurance note:** where this document touches insurance it describes VES's stated market. Nothing here is a claim about the DSES core in that market. We make no claim that it reduces losses or predicts claims.

### 1.1 Summary of the read

VES and the DSES core start from the same diagnosis. VES Section 10 states that logs, telemetry, documentation and traces produced after the execution boundary are insufficient to establish decision-state. DSES Annex E states the same thing as an experiment: hand a reviewer an ordinary platform log and a conformant package for the same decisions, ask the ten reconstruction questions of both, and measure the difference.

They diverge on the primitive. VES defines one boundary, the execution boundary, at which a judgement becomes a committed act, and requires the full decision-state at that moment to be captured, sealed, timestamped and later verifiable. The DSES core defines an ordering: a human judgment committed before designated AI output was presented through the governed workflow, the presentation itself, and the judgment after it. VES's own reconstruction questions ("what did the human see", "where did judgement enter", from the 2026-09-01 post) are answerable only if the record carries that ordering. VES v1.1 does not require it.

They also diverge on what a record is permitted to claim about itself. VES states that only its top evidence level provides deterministic proof of decision conditions. The DSES core states that an unwitnessed hash chain does not establish historical immutability against its own operator, makes no completeness claim at any assurance level, and lists what its mechanisms make visible without preventing.

### 1.2 Crosswalk

Direction of every relationship: the VES concept relative to the DSES concept.

| VES concept (v1.1) | DSES concept | Relationship | Note |
|---|---|---|---|
| Execution boundary (Def. 2): the point at which a judgement becomes a committed organisational act | Committed decision state (v0.1); in the clinical companion profile, `HUMAN_ASSESSMENT_COMMITTED` (T1) and `FINAL_ASSESSMENT_COMMITTED` (T3) with `AI_OUTPUT_PRESENTED` (T2) between them | `broader-than` | VES has one boundary. The DSES ordering claim needs two commitments and the presentation event between them. A VES execution boundary maps most naturally to T3. Nothing in VES v1.1 requires a pre-exposure commitment. |
| Decision-state (Def. 2): inputs, authority, constraints, system outputs and conditions that "existed and were actively relied upon" | Information set at commitment; context snapshot with `reader_access_state`; presentation recorded as an event | `broader-than` in scope, and it asserts more | VES requires the record to state what was relied upon. The DSES core records what was presented through the governed workflow and declines to assert perception or reliance (presentation is not perception, companion profile Section 2). Reliance is an inference the DSES core leaves to the reader. |
| Evidence Pack (Def. 2) | Sequence bundle (companion profile); OL package (core Section 10) | `broader-than` | Both are integrity-bound containers. VES specifies required content categories (Section 3); the DSES core specifies event vocabulary, payload fields, canonical form and chain structure. |
| Point-in-time timestamp "or equivalent temporal anchor" (Sections 3, 5) | Event `stamp` (asserted); ordering from the chain, never from the clock; `anchor_evidence_recorded` (core 3.4.1) | `narrower-than` on ordering, `identical` on intent for timestamps | The DSES core treats a wall-clock stamp as an assertion by the emitter and derives order from chain position, so decreasing stamps can be conformant. VES Section 5 forbids retroactive rewriting of stamps but does not state how a verifier detects it. |
| Integrity mechanism: "a cryptographic hash, seal, or equivalent" (Section 4), algorithm and canonical form not stated on the pages read | SHA-256 over RFC 8785 (JCS) canonical form; two-level events; append-only checkpoint log (core Sections 3.1 to 3.3) | `broader-than` | VES leaves the mechanism to the implementer. The DSES core specifies it so that two implementations hash the same bytes. |
| "Sealed" (evidence level L4; certification level Sealed) | Hash-bound, finalized (companion profile permitted terms) | `no-counterpart` by decision | The companion profile bans "sealed", "tamper-proof" and "immutable" because they imply historical immutability, which an operator-held record cannot establish (core 2.2). The companion profile uses "hash-bound" for the same mechanical property. |
| VES-Certified: timestamp anchored to an external or verifiable source; verifiable without reliance on the originating system (certification page) | External anchoring under an external trust root: DSES-ANCHOR-v1 receipt over artifact hash, anchor time and authority identity, checked against a reader-supplied trust store, never against package-carried keys (core 3.4.1, 3.5); threat model A1 to A7 (core 2.4) | `identical` in intent, `broader-than` in specification | Same goal. The DSES core names the receipt format, the external trust store, the adversaries it holds against, and reports anchor trust as an attestation rather than a verified property. The anchoring mechanism is not stated on the VES pages read. |
| Verifier (Def. 2): a party assessing integrity, timing and completeness without reliance on internal assertions | Reference verifier (software) plus external trust root; conformance report as a dated document with named signer, scope and limitations (`CONFORMANCE-POLICY.md`) | `broader-than` | VES defines the verifier as a party; the DSES core defines the verifier as executable rules a reader can re-run, and keeps the human report separate. |
| "Only VES-L4 provides deterministic proof of decision conditions" (framework page) | Core 2.2 (unwitnessed chain does not establish historical immutability against its operator), 2.3 (made visible, not prevented), Section 13 (no completeness claim at any assurance level, no historical-immutability claim absent a named trust anchor) | `no-counterpart` | The DSES core makes the opposite statement about its own records, on purpose. |
| Decision-state "complete and materially sufficient" (Sections 3, 6); omission is non-conformance | No completeness claim at any assurance level (core Section 13); population curation, adjudicator shopping and selective emphasis listed as made visible, not prevented (core 2.3) | `no-counterpart` | VES requires completeness and makes its absence a conformance failure. The DSES core refuses to assert completeness from a record. |
| Held Conditions (Section 3.1): controls must be shown to have actively held at execution, not merely defined | v0.1 I3(a): AI output release mechanically predicated on a prior committed decision state; companion profile Section 2: record conformance is not implementation conformance | `identical` concern, opposite handling | VES puts the burden on the record. The companion profile states that a conformant record cannot establish that the producing application enforced the workflow it represents, and moves that question to a separate implementation-assurance lane. |
| Accountable role, actor, or authority context; validity of authority at execution (Section 3) | Actor on events; evaluation actor and team-reliance trajectory (core 8.3, Annex E Q6) | `broader-than` | The record carries who acted and distinguishes baseline actor from evaluating actor. It does not evaluate whether authority was valid. |
| Defensibility failure (Section 9): a decision without verifiable decision-state "is exposed under scrutiny" | Sequence is not fault (core 9.6); eleven determination fields the schema rejects; liability-direction neutrality | `no-counterpart` | VES frames the consequence of a missing record as exposure of the decision. The DSES core makes no statement in either direction about what a record or its absence means for fault. |
| Reconstruction limitation (Section 10) | Annex E comparator experiment; the reconstruction burden concept is not named in DSES | `identical` diagnosis | Stated as a prohibition in VES and as a measurable test in DSES. |
| Certification levels (Compliant, Verified, Certified), marks, VES Certification Identifier (VCID) | None. Conformance is reported in a document, never a badge, seal, listing or directory entry (`CONFORMANCE-POLICY.md`). A certification mark, if ever, is a future distinct mark. | `no-counterpart` by decision | Recorded as a difference in posture, not a defect on either side. |
| Regulatory alignment: EU AI Act, DORA, Digital Services Act | Annex A (informative) regulatory context; ACR-SIIM practice parameter mapping in the acceptance-test template | `broader-than` in reach | VES maps to EU horizontal instruments; the DSES core and its template map to US clinical-imaging instruments. |
| Scope: consequential human, organisational or system-assisted judgement (Section 1) | Criterion-evaluable tasks (core 1.1); clinical profile for imaging interpretation; core is domain-neutral with domain profiles layered on | `broader-than` | VES is written for any consequential decision. The DSES core is narrower on purpose and wider on domain than its first profile suggests. |

### 1.3 What the DSES core specifies that VES v1.1 does not, on the pages read

- An ordering primitive: judgment committed before designated AI output was presented through the governed workflow, and the judgment after.
- Typed prior exposure on the pre-exposure commitment (companion profile draft.9, in preparation), so a naive baseline and a conditioned baseline are distinguishable on the face of the record.
- The transition matrix: eight named states and two focal conditional rates with mandatory paired reporting, computed from the record.
- Hash algorithm, canonical form, event vocabulary, payload fields and chain structure.
- An anchor receipt format and an external trust store the verifier must use.
- A threat model naming the deploying operator as the adversary.
- Executable adversarial suites shipped with the specification, including the fixture that asserts an unwitnessed full-history rewrite is not reported as detected.
- Published non-claims (core Sections 2.2, 2.3, 13; companion Section 2).

### 1.4 What VES has that the DSES core does not

- A certification program with named levels, marks, and an identifier scheme.
- A version labeled stable (v1.1) rather than a release candidate.
- A regulatory alignment statement covering EU horizontal instruments.
- A named economic quantity, Reconstruction Burden, with trade-press circulation.
- Product deployments described on the steward's site (claims, parametric triggers, consent evidence).

### 1.5 Naming observations, recorded as facts

- The Insurance-Edge.Net piece of 2026-09-01 expands VES as "Verified Evidence Standard". The specification and stewardship pages expand it as "Veriscopic Evidence Standard".
- The framework page lists marks as Verified, Sealed, Anchored, Platinum. The certification page lists levels as VES-Compliant, VES-Verified, VES-Certified.
- VES-Verified is defined as validated against "the VES schema". A schema was not found on the pages read.

### 1.6 Position

Adjacent, not nested. The DSES core is not a subset of VES and this document does not describe it as a VES implementation. The one interoperability path this document names: an application profile of the DSES core for an insurance workflow could emit its sequence bundle as one of the "system outputs relied upon" inside a VES Evidence Pack, carrying the ordering the pack otherwise lacks. That path runs one way.

### 1.7 Questions the public text does not answer

These are the questions to put to the steward before any relationship stronger than "adjacent" is asserted.

1. Is a schema published for VES-Verified validation, and where?
2. Which hash algorithm and canonical serialization does an Evidence Pack use, so that two implementations seal the same bytes?
3. By what mechanism is a VES-Certified timestamp anchored, and what trust root does the verifier use?
4. Within a decision-state, can a system output be distinguished from the human's own judgment, and is the order in which they entered the state represented?
5. Does the "actively relied upon" requirement in the decision-state definition rest on an assertion by the producing system, or on something a verifier can check?
6. Is there a stated position on what a conformant record does and does not establish about the producing system's enforcement of the workflow?

---

## Entries pending

ACR Assess-AI, IEEE P3867, Joint Commission RUAIH, IHE Radiology, OpenTelemetry. Each was classified in the 2026-08-24 adoption research as a complement rather than a competitor; each gets an entry here once its public text has been read against the rules above.
