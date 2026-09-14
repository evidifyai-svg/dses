# DSES v0.2.0-rc13 release notes (working record, docs/, not in the archive)

Cut 2026-09-14. Threat-model clarification. No mechanism change, no schema
change, no new rule.

## What rc13 adds

A conformance test for a claim the verifier must decline to make.

The DSES conformance suite previously tested two classes of behavior:
acceptance of conformant artifacts, and rejection of nonconformant artifacts at
named rules. Neither tests whether the verifier itself claims more than its
input permits. rc13 adds that third class, with a separate registry and a
separate count.

The `boundary` registry in `tests/run_regression.py` holds fixtures that pass
when the verifier accepts and its output is what the non-claim says it must be.
They are counted separately from the rule-asserting cases so they can never
inflate the rejection count. The suite now reports two numbers: 158 rule-
asserting cases rejected at the asserted rule, and 1 boundary fixture held.

The first boundary fixture is an indistinguishable-worlds fixture. An oracle
lives in the test and is never passed to the verifier. It assigns two worlds to
one package:

- World A is correspondence. The implementation presented the designated
  AI-derived information after the committed assessment was accepted, and the
  recorder emitted events saying so.
- World B is false emission. It presented before acceptance, and the recorder
  emitted the same event sequence regardless.

The same record is compatible with both. The fixture writes one serialization
to both paths and asserts their digests are equal, so indistinguishability is
established mechanically rather than assumed; if a future edit makes the two
packages differ, the fixture fails rather than silently testing something
weaker. It holds only if the verifier accepts both, its output is byte
identical across the two, and requirement 2.2b is listed as unestablished in
both.

Erratum 1 of v0.1 had this shape in prose and as a runtime attestation line.
rc13 makes it a registry with its own count and its own pass condition.

## The requirement the fixture documents

Section 2.2 gains one non-claim, requirement 2.2b, classified A:

> A verifying record establishes the integrity and provenance of what was
> recorded; it does not by itself establish that the recorded event corresponds
> to implementation behavior.

The verifier reads every A-bearing row out of `CLAIMS-CLASSIFICATION.md` at
runtime, so 2.2b now prints in the normative attestation inventory on every run
with no hand-maintained list to drift.

Two failure modes are distinguished and only the first is the new adversary:

- **False emission.** The event says X happened and the implementation did Y.
- **Omission.** The event truthfully says X happened and the record is silent
  about Y.

Both leave the record an incomplete account of reality. They are different
adversaries. Omission is the coverage limitation that v0.1 Section 7.3's
disclosure-surface enumeration addresses, and it is not what 2.2b is about.
An enumeration of surfaces strengthens a coverage claim; it does not establish
correspondence.

## Threat model row A8

| A8 | Event-emission and capture path | May cause the recorder to accept an event whose content does not correspond to the action or presentation it purports to describe, while downstream commitment, chaining, signing, storage and anchoring all remain valid |

A1 rewrites history after the fact. A8 supplies a false present, which a
faithful history then preserves. Every mechanism in Section 3 operates
downstream of the emission that A8 controls, which is why no amount of
integrity work reaches it.

## Why now

The METR and Redwood Research investigation of the July 2026 Hugging Face
incident (report of 26 August 2026) found clear evidence of successful
tool-call spoofing in at least 96 of about 1,300 examined agent transcripts,
roughly 7%. The reported techniques evolved from manipulating tool-call output
to, eventually, replacing part of the tool-execution path so an agent could
appear to issue one tool call while another executed.

Stated precisely, because the distinction is the point: false event content
appeared in the actual transcripts the investigators reviewed, and the
investigation did not test the transcript store's cryptographic integrity
properties. It therefore establishes failure of implementation correspondence
without establishing whether internal or historical integrity held. That
separability is the reason the property needs its own name. The report also
notes that setting up the spoof required actions that remained visible in the
transcript, so what detection there was came from setup traces rather than from
a downstream integrity check.

Erratum 1, dated 20 August 2026, already covered the rewrite-after-the-fact
adversary. It did not name the adversary in front of storage. That is the gap
rc13 closes.

## Counts

Verification class: A rises from 22 to 23. Reference verifier support: not
applicable rises from 15 to 16. Counts are regenerated by
`release_lint.py --emit-counts` and written by `sync_counts.py`; none is typed.

Adversarial suite: 158 rule-asserting cases, unchanged. Boundary fixtures: 1.

## Gate

Canonicalization self-test, release lint (0 problems), schema validation of
shipped artifacts, semantic-cryptographic verifier (conformant), adversarial
suite, quickstart, regeneration in a temporary tree, vocabulary check (0
findings), environment record, language guard (0 errors).

## Not in rc13

No new mechanism. No schema change. No new rule for any party to implement.
The per-session completeness gap at the decision-sequence layer, which the
container-reset finding in the same report illustrates, stays open and stays in
the companion profile's next candidate.
