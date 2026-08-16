# Decision-Sequence Evidence Schema (DSES)

**Version:** 0.1.0 (Draft for public comment)
**Date:** August 15, 2026
**Author:** Joshua M. Henderson, Ph.D. (Evidify LLC, East Orange, NJ)
**Status:** Open specification. Comments and implementation reports welcome.
**Specification license:** CC BY 4.0
**Reference schema and code license:** MIT
**Supersedes:** `@evidifyresearch/event-schema` v0.1.0 (npm, March 22, 2026), which this document generalizes and extends.

---

## Abstract

Organizations deploying AI in consequential decision workflows increasingly know which AI system ran, what output it produced, and what the final human decision was. They often cannot establish what the human believed before AI exposure, exactly when and in what form AI output reached the human, or how the human's decision changed afterward. Existing audit infrastructure records that a decision occurred; it does not preserve the decision *trajectory*.

DSES defines a minimal, vendor-neutral event vocabulary for representing human-AI decision sequences: the human's committed decision state, the availability and presentation of AI output, the class of information the AI output conveyed, subsequent human revision, and the final accountable decision. It defines an exposure ontology that replaces the binary "did the human see AI output" with a graded model of information state. It defines integrity classes that range from ordinary application logging to cryptographically enforced sequential disclosure, so that the strength of an evidentiary claim can be matched to the strength of the mechanism that produced it.

DSES is a semantic layer. It does not replace model performance monitoring, AI governance platforms, clinical orchestration systems, or interoperability standards. It defines the evidence primitive those systems currently lack, and it maps onto HL7 FHIR (AuditEvent, Provenance), IHE Radiology AI profiles, DICOM, and OpenTelemetry rather than competing with them.

---

## 1. The reconstructability principle

This specification exists to serve one normative principle:

> **For consequential human-AI decision workflows, an organization should be able to reconstruct the sequence and material information state of human and AI contributions, at a level of assurance proportionate to the risk of the decision and the intended use of the AI system.**

Two clarifications govern everything that follows.

**Responsibility is not reconstructability.** The human decision-maker remains responsible for the final decision. Nothing in this specification shifts, dilutes, or reassigns that responsibility. Reconstructability is a property of the *record*: whether it can establish, after the fact, what the human knew, what the AI contributed, and in what order. A record can assign responsibility perfectly while reconstructing nothing. Current records generally do exactly that.

**Sequence is a workflow variable, not a moral claim.** DSES does not assert that any particular ordering of human judgment and AI exposure is clinically superior. Whether sequential disclosure changes decision quality is an empirical question under active study. DSES asserts only that if sequence is not *recorded*, it cannot be *studied*, *governed*, or *established afterward*, and that the record of sequence must be trustworthy in proportion to the claims made on it.

---

## 2. Scope

### 2.1 In scope

- A typed event vocabulary for human-AI decision sequences (Section 4).
- An exposure ontology classifying what kind of information AI output conveys to a human (Section 5).
- An information-state model that determines whether a committed human decision state can be characterized as independent of AI influence, and to what degree (Section 6).
- Integrity classes specifying how strongly the record resists tampering and retrospective reconstruction (Section 7).
- Conformance levels for implementations (Section 8).
- Mappings to FHIR, IHE, DICOM, and OpenTelemetry (Section 9).
- Privacy architecture requirements, including the treatment of timestamps (Section 10).
- Derived metrics definable over conformant event streams (Section 11).

### 2.2 Out of scope

- Model performance, drift, and bias monitoring (see ACR Assess-AI, and commercial model-monitoring platforms).
- AI inventory, policy, and lifecycle governance (see enterprise AI governance platforms).
- Clinical orchestration and result delivery (see imaging AI platforms and PACS vendors).
- Any claim that a particular workflow ordering improves clinical outcomes, reduces automation bias, or reduces liability exposure. Such claims require prospective evidence that does not yet exist and are explicitly disclaimed (Section 13).

### 2.3 Domain neutrality

The primary design target and first implementation domain is diagnostic imaging, because imaging has mature integration standards, structured AI result formats, and established quality assurance infrastructure. The vocabulary is deliberately domain-neutral: the same events describe pathology reads, utilization review, disability determination, claims adjudication, and any other workflow in which a human renders a consequential judgment with AI participation. Domain-specific payload schemas plug into the generic event envelope.

---

## 3. Terminology

**Decision state.** A structured or unstructured representation of a human's judgment about a case at a point in time, sufficient to determine later whether the judgment changed. A committed decision state is one recorded with integrity metadata such that its content and time of commitment can be established afterward.

**Exposure.** Any event by which AI-derived information reaches, or is made available to, a human decision-maker. Exposure is classified by the *kind* of information conveyed (Section 5), not merely by whether it occurred.

**Information state.** The accumulated set of exposure classes that have reached a specific human for a specific case at a specified moment. The information state at the moment of commitment determines the independence class of a decision state (Section 6).

**Sequential disclosure.** An active workflow pattern in which AI output is withheld from the human until a decision state has been committed. Commit-then-reveal is the enforcement pattern in which release of AI output is mechanically predicated on the existence of a committed decision state.

**Actor.** A human or system participant. Human actors are pseudonymous by default (Section 10.4).

**Case.** The unit of decision (a study, an encounter, a claim, a vignette). Cases are referenced pseudonymously in exported data.

The key words MUST, MUST NOT, SHOULD, SHOULD NOT, and MAY are to be interpreted as described in RFC 2119.

---

## 4. Event vocabulary

A conformant event stream is an ordered sequence of typed events. Ten event types are defined. Implementations MAY define additional event types in an extension namespace but MUST NOT redefine the semantics of the core ten.

| # | Event type | Meaning |
|---|---|---|
| 1 | `case_context_created` | A case enters the instrumented workflow. Establishes the case reference, workflow reference, and applicable AI systems. |
| 2 | `context_signal_recorded` | An upstream signal that may carry indirect AI influence reaches the workflow before any direct exposure: a triage system reorders the worklist, a flag marks the case urgent, a routing rule assigns it to a specialist queue. This event exists because indirect exposure contaminates independence claims (Section 6) and is invisible to systems that only log direct display. |
| 3 | `human_state_committed` | A human decision state is committed. The event carries a reference to the decision-state content (or a cryptographic commitment to it, at higher integrity classes) and the actor's information state at the moment of commitment. |
| 4 | `ai_result_available` | An AI system has completed generation of output for the case. Availability is not presentation: this event fires when the result exists, whether or not any human has seen it. |
| 5 | `ai_result_presented` | AI output is rendered, displayed, or otherwise delivered to a specific human actor. Carries the exposure class or classes (Section 5) and the presentation modality. This is the pivotal event most existing infrastructure does not record. |
| 6 | `ai_result_interacted` | The human interacts with presented output: expands it, toggles an overlay, dismisses it, scrolls a generated narrative, accepts or rejects a suggestion. Interaction events refine, but do not substitute for, presentation events. |
| 7 | `human_state_revised` | A previously committed decision state is superseded by a new committed state. The event references both the prior and the new state, permitting computation of what changed after exposure. |
| 8 | `final_decision_committed` | The accountable final decision is committed. Every conformant case sequence MUST terminate in exactly one of these. |
| 9 | `attestation_recorded` | A human records a structured rationale attached to a decision event: an override reason, a disagreement code, an acknowledgment. Optional at all conformance levels. |
| 10 | `integrity_event` | An event about the record itself: an export was generated, a verification was performed, an anchor was published, a gap or fault was detected. Integrity events make the record's own lifecycle auditable. |

### 4.1 Event envelope

Every event carries a common envelope. Field-level definitions and types are normative in the accompanying JSON Schema (`dses-v0.1.schema.json`); the table below is the semantic summary.

| Field | Req | Description |
|---|---|---|
| `event_id` | MUST | Globally unique identifier. |
| `event_type` | MUST | One of the ten core types, or a namespaced extension type. |
| `sequence` | MUST | Monotonic per-case ordinal assigned by the recording system. Ordering claims rest on `sequence` plus integrity class, never on wall-clock timestamps alone. |
| `occurred_at` | MUST | Wall-clock time of the underlying occurrence, as known to the source system. |
| `recorded_at` | MUST | Wall-clock time the recording system durably wrote the event. Divergence between `occurred_at` and `recorded_at` is itself evidence and MUST NOT be silently normalized. |
| `case_ref` | MUST | Pseudonymous case reference. |
| `workflow_ref` | SHOULD | Identifier of the workflow definition in force. |
| `actor` | MUST for human-attributed events | Pseudonymous actor reference, actor type (human, ai_system, service), and role. |
| `ai_system` | MUST for events 4, 5, 6 | Structured identity: system name, vendor, model identifier, model version, deployment identifier. Version identity is mandatory; analysis without it is ambiguous. |
| `exposure` | MUST for event 5; SHOULD for event 2 | Exposure class or classes (Section 5), presentation modality, and a payload reference or payload commitment. |
| `decision_state_ref` | MUST for events 3, 7, 8 | Reference to, or cryptographic commitment to, the decision-state content. |
| `information_state` | MUST for events 3, 7, 8 | The actor's accumulated exposure classes at the moment of commitment (Section 6). |
| `integrity` | MUST | Integrity class of the recording pathway (Section 7) and, at class I2 and above, the event hash and previous-event hash. |
| `source_system` | MUST | The system that emitted the event (PACS, reporting system, AI platform, EHR, study platform). |
| `extensions` | MAY | Namespaced extension payloads. |

### 4.2 Sequencing rules

1. Every case sequence MUST begin with `case_context_created` and terminate with exactly one `final_decision_committed`.
2. `ai_result_presented` MUST be preceded by a corresponding `ai_result_available` for the same AI system and case.
3. `human_state_revised` MUST reference a previously committed state within the same case.
4. At conformance level L3 (Section 8), for workflows designated as sequential-disclosure workflows, `ai_result_presented` MUST NOT precede the first `human_state_committed` for the designated deciding actor, and the enforcement mechanism MUST be documented and classified (Section 7.3).
5. Implementations MUST record events they cannot order (for example, events arriving from a source system without reliable sequencing) with an explicit `ordering: indeterminate` marker rather than assigning an arbitrary order. An honest gap outranks a fabricated sequence.

---

## 5. The exposure ontology

The question "did the clinician see the AI output" is not answerable with yes or no, because AI output reaches humans through channels that convey categorically different information and contaminate judgment in categorically different ways. DSES defines eight exposure classes. An exposure event carries one or more classes.

| Class | Definition | Example | What it contaminates |
|---|---|---|---|
| `PRIORITY` | The case's position, timing, or routing was influenced by AI before the human engaged with it. | Triage algorithm moves a head CT to the top of the worklist. | Prior probability. The reader approaches the case already knowing something flagged it. |
| `PRESENCE` | The human can see that AI output exists for this case, without seeing its content. | A badge indicates "AI result ready." | Expectation. The knowledge that the system generated *something* alters engagement. |
| `CATEGORICAL` | A discrete finding or classification is conveyed. | "Pneumothorax detected." "BI-RADS 4." | The diagnostic hypothesis itself. |
| `LOCALIZATION` | Spatial information directs attention. | Heat map, bounding box, contour overlay. | Visual search. Attention is drawn to regions the model selected, and away from regions it did not. |
| `QUANTITATIVE` | A number conveys magnitude, probability, or measurement. | Malignancy score 0.87; nodule 6.2 mm. | Strength of belief and threshold behavior. |
| `NARRATIVE` | Prose framing is conveyed. | AI-drafted impression or report text. | Diagnostic framing, language, and anchoring on the generated wording. |
| `DIRECTIVE` | A recommended action is conveyed. | "Recommend CTA." "Refer to dermatology." "Deny authorization." | The downstream decision, independent of the human's own diagnostic reasoning. |
| `AGENTIC` | The AI has already acted rather than advised. | An order was placed, a message sent, a claim routed. | The decision space itself. The human is now reviewing an action, not considering advice. |

### 5.1 Ordering of severity

The classes are listed in approximate order of increasing contamination of independent judgment, but implementations MUST NOT collapse them into a single ordinal score. `PRIORITY` and `PRESENCE` are indirect: they alter expectation without conveying content. `CATEGORICAL` through `DIRECTIVE` are direct: they convey the model's substantive output. `AGENTIC` is post-decisional: the action space has already been altered. The analytical uses of these distinctions differ, and a scalar would destroy them.

### 5.2 Composite exposures

A single presentation commonly carries multiple classes. A CAD overlay with a confidence score is `LOCALIZATION` + `QUANTITATIVE`. An AI-drafted report with an embedded recommendation is `NARRATIVE` + `DIRECTIVE`. Exposure events MUST enumerate all classes conveyed, not the most severe one.

---

## 6. Information state and independence

### 6.1 The problem this section solves

A radiologist can render a "pre-AI read" of an image while already knowing that a triage algorithm moved the study to the top of the worklist. Calling that read fully independent would be false. Any framework, including this one's own antecedents, that models independence as a binary "AI seen: yes/no" is vulnerable to exactly this objection, and the objection is correct.

### 6.2 The model

The information state of an actor for a case at time *t* is the set of exposure classes that have reached that actor for that case at or before *t*. Every committed decision state (events 3, 7, 8) MUST record the actor's information state at the moment of commitment.

From the information state, the independence class of a committed decision state is derived:

| Independence class | Condition | Meaning |
|---|---|---|
| `UNEXPOSED` | Information state is empty. | No AI-derived information of any class reached the actor before commitment. The strongest independence claim available. |
| `INDIRECTLY_EXPOSED` | Information state contains only `PRIORITY` and/or `PRESENCE`. | The actor's expectations may have been altered, but no substantive model output reached them. Committed states in this class support a qualified independence claim, and the qualification MUST travel with the claim. |
| `DIRECTLY_EXPOSED` | Information state contains any of `CATEGORICAL`, `LOCALIZATION`, `QUANTITATIVE`, `NARRATIVE`, `DIRECTIVE`. | Substantive model output reached the actor before commitment. No independence claim is supportable for this state. |
| `POST_ACTION` | Information state contains `AGENTIC`. | The actor is reviewing or ratifying an already-executed action. Independence is not the operative concept; oversight quality is. |

### 6.3 Consequences

1. A workflow in which AI triage reorders the worklist can never produce `UNEXPOSED` first reads for flagged cases. It can produce `INDIRECTLY_EXPOSED` reads, and the record will say so precisely. This is a feature. The record tells the truth about the workflow instead of flattering it.
2. Claims built on committed decision states MUST carry the independence class. "The clinician's independent judgment was recorded before AI disclosure" is a supportable statement only for `UNEXPOSED` and, with qualification, `INDIRECTLY_EXPOSED` states.
3. Study designs comparing sequential and simultaneous presentation SHOULD stratify on independence class rather than treating the sequential arm as uniformly unexposed.

---

## 7. Integrity classes

The evidentiary weight of a decision-sequence record depends on how strongly the recording pathway resists tampering, backdating, and retrospective reconstruction. DSES defines four integrity classes. Every event declares the class of the pathway that recorded it, and a case sequence's overall class is the *minimum* class across its events.

| Class | Name | Properties | What it can support |
|---|---|---|---|
| **I0** | Application log | Mutable storage, client-supplied timestamps, no ordering guarantee beyond insertion. | Operational debugging. Not evidence of sequence. |
| **I1** | Controlled log | Append-oriented store, server-assigned timestamps and sequence numbers, access-controlled, no cryptographic binding between events. | Ordinary business-records claims. Sequence assertions rest on trust in the operator and the absence of tampering, which cannot be demonstrated from the record itself. |
| **I2** | Tamper-evident log | Hash-chained append-only event log. Each event carries a cryptographic hash binding it to its predecessor. Decision-state contents are bound by cryptographic commitment (the commitment is recorded before or with the event; the content hash must match on reveal). Exports are self-contained packages verifiable by a standalone offline verifier that recomputes every hash from genesis, independent of the operator. | Demonstrable internal consistency. Any post-hoc insertion, deletion, or modification within the chain is detectable by any third party holding the export. Absolute wall-clock claims still rest on the operator's clock unless anchored (I3). |
| **I3** | Enforced sequence | I2, plus one or both of: **(a) enforced ordering**, in which release of AI output is mechanically predicated on the existence of a committed decision state, so the claimed sequence is not merely recorded but could not have occurred otherwise; **(b) external anchoring**, in which chain heads are periodically committed to an independent timestamping authority (RFC 3161), a transparency-log construction (RFC 6962/9162), or a public timestamp proof (OpenTimestamps), binding the record to external time. | The strongest available claim: the sequence is enforced by mechanism, verifiable by third parties, and anchored outside the operator's control. |

### 7.1 Honest labeling

Implementations MUST NOT present lower-class records with higher-class language. In particular, an I1 audit log MUST NOT be described as tamper-evident, and an I2 record MUST NOT be described as proving wall-clock time absent anchoring. The most common failure mode in current practice is precisely this inflation: ordinary mutable audit tables described as if they were proofs.

### 7.2 Fail-closed requirement

At I3(a), the enforcement mechanism MUST fail closed. If the component that verifies the existence of a committed decision state is unreachable, errors, or times out, AI output MUST be withheld, not released. A gate that fails open is an I2 system wearing an I3 label, and the discrepancy will be found by exactly the adversarial reviewer the record exists to satisfy.

### 7.3 Reference enforcement patterns (informative)

The following patterns satisfy I3(a). They are documented here as public reference patterns; none is proprietary to any implementation.

- **Key-gated release.** The AI output is stored encrypted; the decryption key is released by a server-side function only upon verification of a committed decision state for the requesting actor and case.
- **Database-predicate enforcement.** The datastore itself denies reads of AI output rows unless a matching committed decision state exists, enforced by row-level security policy or equivalent, so that no application-layer path can bypass the predicate.
- **Sole-path enforcement.** Architecture guarantees that exactly one code path can release AI output, that path performs the commitment check, and no alternative surface (API, export, replication, backup read) can disclose the output pre-commitment. The disclosure surface MUST be enumerated and each channel classified.
- **Chain-bound release.** The release event is cryptographically bound to the specific commitment event it was predicated on, so the dependency itself is part of the tamper-evident record rather than an application-level assertion.

### 7.4 Proportionality

Higher integrity classes cost more and constrain workflow more. The reconstructability principle requires proportionality, not maximalism. Routine quality-improvement telemetry is well served at I1 or I2. Research claims about decision sequence require I2. Claims intended to survive adversarial scrutiny, and any workflow marketed as proving independence, require I3.

---

## 8. Conformance levels

Conformance is orthogonal to integrity: levels describe *what* is captured; classes describe *how trustworthily*. An implementation declares both, for example "L2 at I2."

### L1: Exposure provenance (passive)

Captures events 1, 2, 4, 5, 6, 8, and 10. No decision-state capture, no workflow alteration, no added clinician interaction. L1 answers: which AI system ran, whether and when its output was actually presented, to whom, in what exposure classes, and what the final decision was.

L1 is deliberately deployable with near-zero workflow burden and is the recommended entry point for production environments. Most organizations currently cannot answer even the L1 questions.

### L2: Decision trajectory

L1 plus events 3, 7, and 9. Committed decision states with information-state stamps, and revision events linking pre-exposure and post-exposure states. L2 answers: what did the human conclude before substantive exposure, and what changed afterward.

L2 SHOULD prefer decision states that already exist naturally in the workflow (a preliminary structured impression, a draft report, a wet read) over newly imposed capture steps. Added interaction cost MUST be measured and reported.

### L3: Sequential disclosure (active)

L2 plus enforced ordering (Section 7.3) for designated workflows: AI output is withheld until a decision state is committed.

**Regulatory caution, normative.** The timing and form in which information is presented to a device user are part of the device-user interface. Altering presentation sequence for a cleared or approved AI device may implicate its intended use and human-factors characterization. L3 deployments in clinical production MUST be undertaken with the AI vendor's participation and product-specific regulatory analysis, or within research protocols under appropriate oversight. L3 is the scientifically distinctive pattern; it is not a universal default, and this specification does not recommend imposing it on any workflow without that analysis.

---

## 9. Mappings to existing standards

DSES defines semantics, not transport or storage. Implementations SHOULD express DSES events in existing standards wherever those standards can carry the semantics, and MUST document any semantic loss in the mapping.

### 9.1 HL7 FHIR

| DSES | FHIR expression |
|---|---|
| All events | `AuditEvent`, with `type`/`subtype` drawn from a DSES code system, `agent` carrying actor and ai_system identities, `entity` referencing the case and decision-state resources, and `recorded` carrying `recorded_at`. FHIR's guidance that servers should not accept updates or deletes of AuditEvent resources aligns with, but does not by itself satisfy, integrity class I1. |
| Decision states and their lineage | `Provenance` targeting the clinical resource embodying the decision (for example, `DiagnosticReport` or `Observation`), with `Provenance.entity` expressing revision lineage between committed states. |
| Integrity metadata | `AuditEvent.extension` (DSES-defined) carrying event hash, previous hash, and integrity class, pending any future FHIR-native integrity mechanism. |

### 9.2 IHE Radiology

The AI Workflow for Imaging (AIW-I) and AI Results (AIR) profiles already model AI task orchestration and result objects; the AI Result Assessment (AIRA) profile models human assessment of AI results. DSES events 4 and 5 map onto AIW-I/AIR transaction boundaries (result created versus result delivered/rendered); event 6 and attestations map onto AIRA assessment semantics. The principal gap in current profiles is the committed pre-exposure decision state (event 3) and the information-state stamp; an implementation proposal to the IHE Radiology Technical Committee mapping DSES semantics into these profiles is the appropriate vehicle, rather than a new competing profile.

### 9.3 DICOM

Where decision states and AI results are imaging objects, DICOM SR evidence documents and the standard's existing model/version attributes carry payload identity; DSES envelope fields travel as references to SOP instances. DSES does not define new DICOM objects in v0.1.

### 9.4 OpenTelemetry

A case sequence maps naturally onto a trace; events map onto spans or span events with DSES attributes under a `dses.*` namespace; trace-context propagation across PACS, AI platform, and reporting system solves the cross-system correlation problem that defeats most retrospective reconstruction. OTel is transport and correlation only: it contributes nothing to integrity class, and OTel-carried events remain I0/I1 unless written into an I2+ store.

### 9.5 What the mappings do not provide

No existing standard enforces sequencing (I3a) or provides offline third-party verifiability of the full chain (I2 export semantics). Those remain implementation obligations above the standards layer, which is precisely why they are specified here.

---

## 10. Privacy architecture

### 10.1 The timestamp problem

Precise time is part of this specification's value and part of its risk. Under the HIPAA Safe Harbor method, dates more specific than the year are identifiers; a de-identified dataset containing exact event timestamps is not Safe Harbor de-identified. Sequence evidence therefore cannot be casually centralized.

### 10.2 Local raw, central derived

Conformant multi-site architectures MUST keep the raw sequence local to the originating institution and export only derived representations:

| Stays local | May be exported centrally |
|---|---|
| Patient and study identifiers | Site pseudonym, use case, workflow reference |
| Exact event timestamps | Relative time deltas between events; coarsened absolute time strata where permitted |
| Clinician identity | Actor pseudonym or aggregate strata |
| Decision-state contents | Decision-change category (unchanged, refined, reversed), independence class |
| Raw AI output | AI system identity and version, exposure classes |

Where exported derivations still constitute PHI in context, export MUST proceed under a business associate agreement, and de-identification claims MUST rest on Expert Determination rather than Safe Harbor.

### 10.3 The record is about the interaction, not the clinician

Clinician-level reliance and override metrics are one policy decision away from individual performance surveillance, and a specification that enables covert surveillance of the people it instruments will be rejected by them, correctly. Conformant implementations:

- MUST default to aggregate-only reporting of human-behavior metrics;
- MUST document, before collection begins, who may access actor-resolved data, for what purposes, and under what governance;
- SHOULD involve the instrumented clinicians in the design of any metric that could be resolved to an individual;
- MUST NOT repurpose actor-resolved data for performance management absent explicit, documented, prior agreement.

### 10.4 Pseudonymity

Actor and case references in the event stream are pseudonymous. The mapping from pseudonyms to identities is held by the originating institution under its own access controls and is not part of the DSES record.

---

## 11. Derived metrics (informative)

The following metrics are computable over L2+ event streams. They are proposed measures for study, not established clinical standards, and the last three are meaningless without adjudicated ground truth: a decision change is not inherently good or bad, and the raw sequence cannot say which.

**AI influence rate.** Proportion of AI-exposed decisions in which the post-exposure state differs from the pre-exposure state.

**Beneficial correction rate.** Among cases with an incorrect pre-exposure state and correct AI output: proportion in which the final state is correct.

**Harmful reversal rate.** Among cases with a correct pre-exposure state and incorrect AI output: proportion in which the final state is incorrect.

**Appropriate resistance rate.** Among cases with incorrect AI output presented: proportion in which the final state is correct.

**Reliance asymmetry.** P(final state concordant with AI | AI correct) minus P(final state concordant with AI | AI incorrect). Well-calibrated reliance is large and positive.

**Exposure-to-revision latency.** Distribution of time between `ai_result_presented` and `human_state_revised`, by exposure class.

**Sequence effect.** Any difference in the above between sequential-disclosure and simultaneous-presentation conditions, computable only in designed studies with randomization.

All human-behavior metrics are subject to Section 10.3.

---

## 12. Conformance claims

A conformance claim names the specification version, level, and integrity class, and identifies the enforcement pattern where L3 is claimed:

> "This system implements DSES 0.1 at L2/I2: decision-trajectory capture over a hash-chained event log with offline third-party verification."

> "This study platform implements DSES 0.1 at L3/I3: sequential disclosure enforced by database-predicate and key-gated release, with external anchoring via RFC 3161."

Claims MUST be verifiable: an L2+/I2+ claimant MUST make a verifier and a sample export available to any party asked to rely on the claim.

---

## 13. What this specification does not claim

1. **No outcome claims.** DSES does not claim that sequential disclosure, or any capture level, improves diagnostic accuracy, reduces automation bias, or changes liability outcomes. Peer-reviewed argument exists that decision sequence is an unmeasured variable with evidentiary and measurement consequences, and experimental evidence exists that erroneous AI recommendations can materially influence expert readers. Whether changing or recording sequence changes outcomes is under prospective study. The specification's claims are confined to what a record can and cannot establish.
2. **No compliance claims.** Conformance to DSES does not constitute or imply compliance with, certification under, or endorsement by any regulatory, accreditation, or standards body, including FDA, the Joint Commission, CHAI, ACR, HL7, IHE, or NIST.
3. **No responsibility transfer.** Nothing in a DSES record moves responsibility for a decision from the accountable human to any system, vendor, or record-keeper.

---

## 14. Versioning and governance

This specification uses semantic versioning. v0.x versions are drafts for public comment; breaking changes may occur between minor versions before 1.0. Proposed changes, implementation reports, and mapping corrections are received as issues against the public repository. Decisions for v0.x rest with the author; a multi-stakeholder governance process is intended from 1.0 if independent implementations exist.

**Citing this specification:**

> Henderson JM. Decision-Sequence Evidence Schema, version 0.1. Evidify LLC; 2026. Available from the public repository.

---

## Appendix A. Relationship to prior work by the author

The `@evidifyresearch/event-schema` npm package (v0.1.0, March 22, 2026, MIT) published an earlier ten-category event taxonomy and the commit-then-reveal sequence for a specific research platform. DSES v0.1 generalizes that work: it separates the semantic layer from any implementation, adds the exposure ontology and information-state model, replaces the binary independence assumption, and defines integrity classes so that commit-then-reveal takes its correct place as one enforcement pattern at the highest assurance class rather than the definition of the category.

## Appendix B. Design rationale for the exposure ontology (informative)

The ontology's classes were derived from the channels observable in deployed imaging AI: triage reordering (PRIORITY), result badging (PRESENCE), finding flags (CATEGORICAL), CAD overlays (LOCALIZATION), scores and measurements (QUANTITATIVE), generated report text (NARRATIVE), care recommendations (DIRECTIVE), and autonomous actions (AGENTIC). The classes generalize outside imaging without modification: a prior-authorization queue sorted by a propensity model is PRIORITY exposure; a draft denial letter is NARRATIVE + DIRECTIVE; an auto-adjudicated claim is AGENTIC. Domain profiles specify payload schemas per class; the classes themselves are fixed.
