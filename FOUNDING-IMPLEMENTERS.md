# DSES Founding Implementers

The program exists to produce external implementation evidence, not endorsements.
Participation does not make an organization or product conformant, and no
implementation is counted until the evidence described below is public.

## Program success criteria

By August 2027, the program aims to publish:

- five named implementing organizations;
- at least two independent, non-reference emitters maintained outside Evidify;
- three real deployments, which may include a reader study, a pre-deployment
  acceptance test, or a production passive-logging workflow;
- five implementation or interoperability reports;
- three conformance transcripts, only if the requirements in
  `CONFORMANCE-POLICY.md` are actually met; and
- three named human expert reviews spanning protocol/cryptography, statistics,
  and health law or clinical governance.

The public baseline remains the counts in `SCORECARD.md`. Private pilots,
intentions, copied examples, same-maintainer forks, and AI-only implementation
attempts do not increment the independent-implementation count.

## What qualifies as a founding implementation

An implementation is credited when all of the following are public:

1. A named organization and accountable human technical lead.
2. A bounded workflow and exact DSES version.
3. An emitter, adapter, or independently written verifier exercised outside the
   reference example. At least two program implementations must be independently
   engineered and maintained without Evidify's reference emitter code.
4. A synthetic, deidentified, or locally reproducible evidence package that
   exposes no patient or confidential production data.
5. Reproduction instructions and a verification transcript that name the checks,
   failures, environment, artifact hash, and limitations.
6. A short implementation report covering architecture, event boundaries,
   capture level, integrity class, interoperability mappings, workflow burden,
   privacy controls, and unresolved specification ambiguities.
7. Correct public labeling. Schema-valid, compatible, and conformant are not used
   as synonyms.

An implementation may report a failed or partial result. A well-documented
failure can reveal an interoperability defect and still qualify as an
implementation report, but it does not create a conformance transcript.

## When a count moves

Each count in `SCORECARD.md` is derived from files published in `registry/`, or
in `docs/reviews/` for named reviews, and moves only in the pull request that
publishes them. These rules were written in November 2026 while every count
was zero, so that no count is defined after the evidence for it arrives.

- **Implementing organizations.** One per named organization with a published
  entry whose own staff built or maintain an emitter, adapter, or verifier,
  whether independently engineered or built on the reference code, and whatever
  the verification result. An organization that supplies readers, cases, or a
  site to a study run on Evidify infrastructure is a study site, not an
  implementing organization.
- **Independent implementations.** A published entry whose implementation was
  engineered and is maintained outside Evidify, reuses no reference emitter
  code, and names an accountable human technical lead. Use of AI tools is
  disclosed in the entry and does not by itself disqualify an implementation.
  An attempt with no accountable human engineer is not counted.
- **Real deployments.** A published entry with a bounded workflow in which real
  actors, not test or synthetic sessions, produced records under a named
  version of the DSES specification. The entry states the setting (reader study, acceptance test, or
  production passive logging), the dates of the first and last record, and an
  aggregate record count. The count is of workflows, not emitters. A deployment
  that runs on the reference implementation counts as a deployment, is labeled
  as using the reference emitter, and moves no implementation or organization
  count. A study that is designed, approved, or loaded with cases but has
  recorded no real session is anchoring, not a deployment.
- **Implementation or interoperability reports.** One per report published
  under `registry/reports/` from the templates there. A report of a failed or
  partial result counts. The scorecard row read "Interoperability reports"
  through October 2026 while this document defined the target as five
  implementation or interoperability reports; the row now carries this
  document's wording, and the target is unchanged.
- **Conformance transcripts.** One per transcript listed under
  `registry/transcripts/`, which requires both conditions of
  `CONFORMANCE-POLICY.md`. A recorded run with failures is evidence for an
  implementation report and is not a conformance transcript.
- **Named expert reviews.** One per attestation published in `docs/reviews/`
  under the reviewer's name. An attestation with objections counts. A review in
  progress, or one given only in conversation, does not. Any relationship
  between the reviewer and the author or Evidify LLC is stated in the
  attestation itself, so that a reader can judge for themselves. The count is
  of named reviews and is not a statement about any reviewer's independence.

`registry/tools/check_registry.py` applies these rules to the published files
and fails when the scorecard disagrees.

## Participation boundaries

- No patient-level data needs to be public.
- Raw actor-resolved sequences should remain local; public artifacts should be
  synthetic, deidentified, or aggregate.
- The program will not credit a workflow whose primary purpose is covert
  individual surveillance, performance ranking, or unsupported adverse action.
- Sequence evidence is liability-direction-neutral. Reports must not assign
  fault, infer causation, or claim legal protection from the record alone.
- There is no fee or permission requirement to implement the open specification.
  Any separate implementation support is outside the conformance decision.

## Suggested first cohort

The intended mix is two clinical-AI vendors or product teams, one independent
research study, one health-system pre-deployment evaluation, and one technically
different health-IT, registry, or research-platform implementation. At least one
vendor implementation should emit DSES without Evidify in its runtime path.

## Propose an implementation

Open a GitHub issue titled `[Founding Implementer] organization or project` with:

- public or private-until-launch status;
- workflow and intended evidence question;
- targeted DSES version, level, and integrity class;
- implementation language and whether reference emitter code will be reused;
- expected synthetic artifact and report date; and
- the accountable human lead.

If the organization cannot be named publicly before launch, send the same fields
to `josh@evidify.ai`. It is not added to the public scorecard until the evidence
is published.
