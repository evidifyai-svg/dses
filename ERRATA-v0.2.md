# ERRATA: DSES v0.2.0

**Applies to:** DSES v0.2.0, once published.
**Status:** No errata. Version 0.2.0 is not yet released, and no erratum can
exist against unpublished text.

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
