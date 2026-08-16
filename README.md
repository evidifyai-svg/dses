# Decision-Sequence Evidence Schema (DSES)

**An open, vendor-neutral vocabulary for evidence of how humans and AI actually make decisions together.**

Version 0.1.0 (draft for public comment) · Spec: CC BY 4.0 · Schema and examples: MIT

---

## The problem

Organizations deploying AI in consequential decisions increasingly know which model ran, what it output, and what the final human decision was. They usually cannot establish three things that matter more:

1. **What the human concluded before AI exposure.** A pre-AI judgment and an AI-influenced judgment collapse into one blended record.
2. **Whether, when, and in what form AI output actually reached the human.** "Result generated" and "result shown to this person" are different events. Almost nothing logs the second one.
3. **What changed afterward.** A human miss corrected by AI, a correct human read reversed by wrong AI, and independent agreement all produce identical final-report concordance statistics.

Model monitoring watches the model. Governance platforms watch the paperwork. Nothing watches the interaction. DSES defines the missing evidence primitive.

## What's here

| File | What it is |
|---|---|
| [`DSES-v0.1.md`](DSES-v0.1.md) | The specification: event vocabulary, exposure ontology, information-state model, integrity classes, conformance levels, standards mappings, privacy architecture. |
| [`dses-v0.1.schema.json`](dses-v0.1.schema.json) | Normative JSON Schema (draft 2020-12) for the event envelope. |
| [`example-sequence.json`](example-sequence.json) | A complete worked case sequence: a liver MRI read at conformance L3, integrity I3, including an indirect triage exposure that correctly downgrades the independence claim. |

## Core ideas, in four sentences

**Ten events** describe any human-AI decision sequence, from `case_context_created` through `human_state_committed`, `ai_result_presented`, and `human_state_revised` to `final_decision_committed`. **Eight exposure classes** (PRIORITY, PRESENCE, CATEGORICAL, LOCALIZATION, QUANTITATIVE, NARRATIVE, DIRECTIVE, AGENTIC) replace the false binary of "AI seen: yes/no," because a worklist reordered by triage AI and an AI-drafted report contaminate judgment in categorically different ways. **Four integrity classes** (I0 application log through I3 enforced sequence) tie the strength of any evidentiary claim to the strength of the mechanism that produced the record, so an ordinary audit table can no longer borrow the vocabulary of a proof. **Three conformance levels** separate passive exposure provenance (deployable today, near-zero workflow burden) from decision-trajectory capture and from active sequential disclosure (the research frontier, with explicit regulatory cautions).

## What DSES is not

- Not a model-monitoring product, a governance platform, or an orchestration layer. It maps onto FHIR AuditEvent/Provenance, IHE Radiology AI profiles, DICOM, and OpenTelemetry rather than replacing them.
- Not a claim that any workflow ordering improves outcomes, reduces automation bias, or reduces liability. Those are open empirical questions under prospective study. DSES claims only that unrecorded sequence cannot be studied, governed, or established afterward.
- Not a surveillance tool. The specification requires aggregate-only human-behavior reporting by default and prohibits repurposing actor-resolved data for performance management absent prior documented agreement.

## Status and how to engage

This is a v0.1 draft published for public comment. Implementation reports, mapping corrections, and proposed changes are welcome as issues. Breaking changes may occur before 1.0. A multi-stakeholder governance process is intended from 1.0 if independent implementations exist.

The schema generalizes and supersedes [`@evidifyresearch/event-schema`](https://www.npmjs.com/package/@evidifyresearch/event-schema) v0.1.0 (March 2026).

## Citing

> Henderson JM. Decision-Sequence Evidence Schema, version 0.1. Evidify LLC; 2026.

## Author

Joshua M. Henderson, Ph.D. · Evidify LLC, East Orange, NJ · josh@evidify.ai
