# ERRATA: DSES v0.2.0

**Applies to:** DSES v0.2.0, minted October 18, 2026.
**Status:** Two errata recorded November 1, 2026, both against
`RELIANCE-CONTEXT-EXAMPLE.md`. v0.2.0 text remains published unaltered; these
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

## Erratum 2: The claim that the Wilson interval's independence assumption is violated

**Section and original text.** `RELIANCE-CONTEXT-EXAMPLE.md`, under "Design
structure of the denominator, and panel agreement": "One reader and three cases
behind three instances is a repeated-measures structure, not three independent
trials, and the artifact says so rather than leaving a committee to assume
otherwise. The interval below is computed under an independence assumption
these counts show to be violated."

And under "What the context changes," second paragraph: "**And the interval is
optimistic.** The three instances come from one reader, so they are clustered
rather than independent, and the Wilson interval assumes independence. Six to
seventy-nine per cent is the narrow reading. The design counts are disclosed so
that a statistician receiving this artifact can inflate the interval
accordingly instead of having to ask for the raw data first."

**Problem.** The counts do not show the assumption is violated. With one reader
and three distinct cases, the Wilson interval is a statement about this reader
on cases drawn the way these were, and treating the three as exchangeable draws
is the ordinary reading of a single-reader binomial interval. Clustering by
reader matters when a rate is generalized across clinicians, which this artifact
does not do. Whether the three cases are exchangeable depends on how cases were
assigned, a sampling question the assignment artifact bears on and the design
counts alone cannot settle. A reader would reasonably conclude that the interval
is known to be too narrow and should be inflated. That conclusion is not
supported.

**Corrected text.** First passage: "One reader and three cases behind three
instances. The interval below treats the three as exchangeable draws from the
cases this reader could have met under this assignment, which is the reading a
binomial interval for one reader supports. It describes this reader on cases
like these. It does not describe clinicians in general, and no estimate from one
reader can."

Second passage: "**And the interval is about this reader only.** Three instances
from one reader support a statement about that reader on cases drawn the way
these were. Whether the three are exchangeable depends on how cases were
assigned, which the assignment artifact records and the counts alone cannot
settle. The design counts are disclosed so that a statistician receiving this
artifact can choose the sampling model, and widen the interval if the assignment
warrants it, without first asking for the raw data."

**Consequential edits.** None in the artifact, the schema, or the verifier. The
specification's requirement that design structure be disclosed stands; only the
example's interpretation of it changes.

**Why an erratum.** The original text asserted a statistical fact the design
counts do not establish. The honest-labeling rule applies to statements about
uncertainty as much as to statements about integrity.

**Provenance of both findings.** Found by the author on November 1, 2026, while
checking an AI-assisted critique of the published example against the artifact.
No named expert reviewer is credited because none made the finding.

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
