# ERRATA: DSES v0.2.0

**Applies to:** DSES v0.2.0, minted October 18, 2026.
**Status:** Three errata recorded November 1, 2026, all against
`RELIANCE-CONTEXT-EXAMPLE.md`, and one open methods question recorded as not an
erratum. v0.2.0 text remains published unaltered; these
errata travel with it. The process for recording them is below the entries.

## Erratum 1: The count of decision-opportunities outside the RAIR denominator

**Section and original text.** `RELIANCE-CONTEXT-EXAMPLE.md`, "What the context
changes," third paragraph: "It is the three cases where this reader was wrong
and the AI was right. Twenty-five of the reader's other decision-opportunities
are not in it."

**Problem.** The artifact the example renders
(`examples/derived/derived-rair-subject-0417-v1.json`) records 10 assigned
decision instances, 8 metric-eligible, and a denominator of 3. Nothing in it
supports twenty-five. A reader would reasonably conclude the subject had about
28 decision-opportunities in the window, and that the denominator was a far
smaller slice of the reader's work than it is. The verifier recomputes every
figure in the artifact; it does not check numbers written in the prose around
it, and this one was not drawn from the artifact.

**Corrected text.** "It is the three cases where this reader was wrong and the
AI was right. Five of the reader's other metric-eligible instances, and seven of
the ten assigned, are not in it."

**Consequential edits.** None in the artifact or the specification. The next
version adds a check that every count stated in a rendered example is present in
the artifact it renders.

**Why an erratum.** The example is the part of the release addressed to review
bodies and counsel. A wrong denominator in the one document written to show how
a denominator must travel is the failure the reliance context exists to prevent.

## Erratum 2: "Never adjudicated" for a case that was adjudicated

**Section and original text.** `RELIANCE-CONTEXT-EXAMPLE.md`, "What the context
changes," fourth paragraph: "Any statement about this reader's reliance has to
sit beside the reader's own error rate, the AI's error rate, and the fact that
one case was not commensurable and one was never adjudicated."

**Problem.** The paragraph describes the eight metric-eligible cases. Among them
the artifact records adjudication status as 7 determinate and 1 indeterminate,
and Annex B of the specification describes that case as "an indeterminate
adjudication": it was
adjudicated, and the panel reached no determinate conclusion. The two cases the
artifact counts as not adjudicated are among the ten assigned instances and are
not metric-eligible. A reader would reasonably conclude that one eligible case
lacked adjudication altogether, which conflates two categories the schema keeps
apart.

**Corrected text.** "Any statement about this reader's reliance has to sit
beside the reader's own error rate, the AI's error rate, and the fact that one
case was not commensurable and one was adjudicated without a determinate
conclusion."

**Consequential edits.** None in the artifact or the specification.

**Why an erratum.** Indeterminate and not adjudicated are distinct categories
in the reliance context precisely so that a case the panel could not resolve is
not mistaken for a case nobody reviewed. The example blurred the distinction it
exists to show.

## Erratum 3: The length of the observation window

**Section and original text.** `RELIANCE-CONTEXT-EXAMPLE.md`, "The same artifact,
as DSES requires it to travel": "Observation window: 2026-03-01 to 2026-06-30,
121 days". And "What the context changes," sixth paragraph: "121 days, inside
the 180 authorised by governance."

**Problem.** The artifact's window runs from the first instant of March 1 to the
last second of June 30, 2026. That is 122 calendar days, March 1 through June 30
inclusive, and the reference verifier's window check, which works in exact
seconds, reports the span as 122.00 days. The example's 121 is the number of
whole days elapsed between the two instants, one second short of 122. A reader
who checks the stated dates against a calendar counts 122 and would reasonably
conclude that the example miscounted its own window, in the document written to
show how a figure must travel. No conclusion changes: either length is inside
the 180-day maximum the governance artifact authorizes.

**Corrected text.** "Observation window: 2026-03-01 to 2026-06-30, 122 days" and
"122 days, inside the 180 authorised by governance."

**Consequential edits.** None in the artifact or the specification. The
rendered-claims check counts the window in calendar days, both dates included.

**Why an erratum.** The published figure is not the one the verifier reports
for the same window. An erratum is required when published text asserts
something the implementation does not establish, whether or not anyone outside
noticed, and a note on how days were counted would leave the number standing.

## Not an erratum: the interval paragraphs

The same critique also questioned the example's statement that the Wilson
interval's independence assumption is violated for this artifact and that the
interval is optimistic. That statement follows Section 8.12, which says an
individual-level metric pools repeated instances within one professional, that
the interval is then computed under a violated assumption and will generally
understate uncertainty, and that a reader holding the design counts can inflate
it. The example is consistent with the normative text, so there is no erratum
against the example. Whether Section 8.12 should treat the subject of a
subject-scoped metric as a cluster at all is a methods question for named
statistical review, recorded here so it is not lost, and it is not decided by
this file.

**Provenance of the three findings.** Found by the author on November 1, 2026:
the first while checking an AI-assisted critique of the published example
against the artifact, the second and third while writing a check that ties every
count in the example to the artifact it renders. No named expert reviewer is
credited because none made any of the three findings.

## Why this file exists before it has content

`ERRATA-v0.1.md` was written five days after v0.1.0 was published, under time
pressure, because public technical review found an overclaim in the integrity
class table. The correction was right and the process around it was invented on
the spot.

This file fixes that process while nothing is at stake. What counts as an
erratum, what does not, and what an entry must contain are decided here rather
than in the week something is found.

## What is an erratum

An erratum corrects **published** text. It applies only to a released version,
never to a candidate.

A defect found in a candidate is fixed in the next candidate and recorded in the
changelog. That is not an erratum, and calling it one would inflate the record.
The rc11 and rc12 candidate work found real defects and none of them appears
here, correctly.

An erratum is required when published text asserts something the implementation
does not establish, or asserts it more strongly than the mechanism supports. It
is required whether or not anyone outside noticed.

## What an entry contains

Each erratum states, in this order:

1. The section and the original text, quoted.
2. The problem, in terms of what a reader would reasonably have concluded and
   why that conclusion is not supported.
3. The corrected text, in full, so the correction can be applied mechanically.
4. Consequential edits elsewhere, listed.
5. Why it is an erratum rather than a silent fix in the next version.

Item 5 is not a formality. The specification requires that a record not be
described with language above its class, and that obligation applies to this
document about itself. Silently repairing published text and letting the old
claim stand uncorrected in the wild is the failure the honest-labeling rule
exists to prevent.

## Standing obligations

The published version is never altered. An erratum travels with it.

An erratum is published when it is found, not when a fix is ready. Sitting on a
finding while it gets repaired is not available, and reviewers are told so
before they agree to review.

A reviewer's finding that becomes an erratum is credited to the reviewer, in an
individual capacity, with their attestation in `docs/reviews/`.

Henderson JM, Ph.D., Evidify LLC.
