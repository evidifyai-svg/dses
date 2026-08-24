# DSES implementation checklist

Record the answer and evidence reference beside each item. A checked box is an
implementation note, not a conformance certificate.

## Scope and claim

- [ ] The workflow question is written before choosing a capture level.
- [ ] The exact DSES version is named; a release candidate includes the full
      `-rcN` suffix.
- [ ] Capture level and integrity class are stated separately.
- [ ] Every claim is limited to evidence the deployed pathway actually records.
- [ ] No text implies that sequence establishes cognition, causation, competence,
      negligence, liability, a standard of care, or outcome benefit.

## Event capture

- [ ] `ai_result_available` is recorded when output exists.
- [ ] `ai_result_presented` is emitted by the rendering or delivery boundary for
      a named pseudonymous actor, not inferred from model completion.
- [ ] All exposure classes conveyed by the presentation are recorded.
- [ ] `occurred_at` and `recorded_at` retain their distinct meanings.
- [ ] Indeterminate order is marked honestly rather than reconstructed.
- [ ] Every case begins with `case_context_created` and ends with exactly one
      `final_decision_committed`.
- [ ] L2+ revisions cite the state they supersede.

## Integrity and verification

- [ ] The event canonicalization and hash preimage are documented.
- [ ] I2+ payload commitments are independently recomputed from disclosed test
      payloads.
- [ ] I2+ event hashes and predecessor links are independently replayed.
- [ ] Any historical rewrite claim names a separately held checkpoint or
      external anchor; a single internally consistent export is not overstated.
- [ ] Any I3 ordering claim documents a deployed fail-closed mechanism and its
      bypass and outage behavior.
- [ ] Verification output records the command, version, artifact hash, operating
      system, runtime, and dependency versions.
- [ ] Failures and unverifiable attestations remain visible in the report.

## Privacy, governance, and secondary use

- [ ] Case and actor references are pseudonymous and contain no direct
      identifiers.
- [ ] Raw actor-resolved sequences remain local by default.
- [ ] Central exports are aggregate or derived unless an approved purpose
      requires otherwise.
- [ ] Access, retention, deletion, and authorized recipients are documented.
- [ ] Human-behavior reporting is aggregate-only by default.
- [ ] Any proposed individual-level use was prospectively governed with a
      declared purpose, minimum cell size, case-mix disclosure, notice and
      access, case-level review, and an appeal path.
- [ ] Data collected for AI evaluation is not silently repurposed for employment,
      credentialing, discipline, litigation, or performance ranking.

## Clinical workflow changes

- [ ] Passive logging adds no unreviewed delay or user-interface change.
- [ ] Any change to the timing or presentation of a clinical AI output has
      product-specific vendor, regulatory, safety, and human-factors review.
- [ ] Study or quality-improvement oversight and consent determinations are
      documented where applicable.
- [ ] Stop rules and operational owners are named for a pilot.

## Publication and interoperability

- [ ] A synthetic or deidentified sample export is available to reviewers.
- [ ] Another person can reproduce verification from a clean environment.
- [ ] The implementation report distinguishes schema validation, sequence
      verification, and conformance.
- [ ] Mappings to FHIR, DICOM, IHE, OpenTelemetry, or local logs identify what
      each transport does and does not establish.
- [ ] Public counts, implementation status, and transcripts are updated only
      after their supporting artifacts are public.
