# Implement DSES

This is the shortest route from an existing human-AI workflow to an honest,
verifiable DSES implementation. Begin with the weakest evidence that answers
your real question. Higher capture levels cost more and do not make lower-level
records retroactively stronger.

## 1. Choose the question before the level

| Question | Start with | What it establishes | What it does not establish |
|---|---|---|---|
| Was an AI result actually presented to this actor, when, and in what form? | L1/I1 passive exposure logging | Operator-attributable application records of availability, presentation, exposure class, and final disposition | Tamper evidence, a pre-AI judgment, or independence |
| What state was committed before exposure, and what changed afterward? | L2/I2 decision trajectory | Payload commitments and hash-chain internal consistency for a pre-exposure, exposure, revision, and final sequence | Historical immutability without a separately held checkpoint; enforced withholding; causation |
| Could the specified AI output have appeared before the commitment? | L3/I3 only after workflow-specific review | The property supported by the deployed fail-closed enforcement mechanism and any separately verifiable anchor | Cognition, decision quality, negligence, or clinical benefit |
| Was the decision correct under a prespecified criterion? | v0.2.0-rc10 outcome layer | Recomputable linkage, adjudication, denominator, and metric claims that the reference verifier implements | Truth beyond the declared criterion, statistical adequacy beyond the stated design, or legal conclusions |

L1 is the default production entry point. L3 is not a universal upgrade. In a
clinical production workflow, changing when a device output appears requires
the AI vendor's participation and product-specific regulatory and human-factors
review, or an appropriately overseen research protocol.

## 2. Run the examples

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
bash quickstart/verify.sh
```

The command validates each event against the v0.1 JSON Schema and checks the
quickstart sequence profile: contiguous ordering, required first and final
events, availability before presentation, information-state derivation,
decision-state lineage, and I2 RFC 8785 event-hash continuity where present.

The two starting flows are:

- [`quickstart/passive-exposure.json`](quickstart/passive-exposure.json): L1/I1.
  Copy the event boundaries into an existing audit or telemetry path. It makes
  no pre-AI-state claim.
- [`quickstart/sealed-sequence.json`](quickstart/sealed-sequence.json): L2/I2.
  It binds synthetic decision and AI payloads by digest and verifies the event
  chain's internal consistency. It carries no external anchor and no enforcement
  evidence, so it must not be described as historically immutable or I3.

The helper examples are deliberately small:

- [`quickstart/python/emitter.py`](quickstart/python/emitter.py) emits an I1
  passive event and provides an RFC 8785 SHA-256 commitment helper.
- [`quickstart/typescript/emitter.ts`](quickstart/typescript/emitter.ts) emits
  an I1 passive event with typed inputs. It deliberately does not improvise an
  RFC 8785 implementation from `JSON.stringify`.

## 3. Add events at real boundaries

1. Create a pseudonymous `case_ref` and, where applicable, a pseudonymous
   `actor_ref`. Do not place direct identifiers in either field.
2. Record `ai_result_available` when the output exists, not when inference was
   merely requested.
3. Record `ai_result_presented` at the component that rendered or delivered the
   output to the named actor. Model completion is not presentation.
4. Enumerate every exposure class conveyed. A worklist reorder (`PRIORITY`) and
   a categorical result (`CATEGORICAL`) are not interchangeable.
5. For L2, commit the pre-exposure state before presentation and record any
   revision as a new state linked through `prior_decision_state_ref`.
6. Terminate the case sequence with exactly one `final_decision_committed`.
7. Preserve `occurred_at` and `recorded_at` separately. Do not repair uncertain
   ordering by inventing a timestamp; use `ordering: indeterminate`.

If the existing workflow already emits FHIR AuditEvent, DICOM, IHE, or
OpenTelemetry records, add a DSES adapter at that boundary. Those transports
can carry and correlate DSES fields, but transport alone does not raise the
integrity class.

## 4. Match cryptography to the claim

For the quickstart I2 profile, the event preimage is the RFC 8785 canonical form
of the complete event with only `integrity.event_hash` omitted. The first event
uses the documented predecessor value `GENESIS`; every later event includes the
full lowercase SHA-256 hash of its predecessor. Decision and exposure payload
references use `sha256:<lowercase digest>`.

A bare digest is binding but not hiding when the decision has a small answer
space. The supplied disclosed payloads are synthetic. A production workflow
that must conceal a low-entropy state until reveal needs a nonce-backed hiding
commitment, controlled nonce disclosure, and verification of both the nonce and
payload. Do not describe an unsalted digest as confidential encryption.

This convention makes the supplied example mechanically reproducible. It does
not turn a single operator-held export into proof of historical immutability.
Preserve a chain head outside the operator, or use a verified external anchor,
before making checkpoint-relative or anchored claims. See `ERRATA-v0.1.md`.

Do not claim I3 from an `enforcement` field alone. A real I3 claim needs the
deployed fail-closed mechanism, its documented threat boundary, and evidence a
reviewer can evaluate.

## 5. Verify, label, and report

Use three separate statements:

1. **What was captured:** named version and capture level.
2. **How it was recorded:** integrity class and the exact trust boundary.
3. **What was verified:** command, artifact hash, environment, checks performed,
   failures, and limitations.

`DSES-compatible` is self-declared. `DSES Conformant` is reserved for the
evidence and public transcript process in `CONFORMANCE-POLICY.md`. Passing the
quickstart examples, copying a helper, or producing schema-valid JSON does not
satisfy that policy.

Before using real data, complete `IMPLEMENTATION-CHECKLIST.md`. When a working
implementation and reproducible report can be made public without patient or
confidential data, see `FOUNDING-IMPLEMENTERS.md`.
