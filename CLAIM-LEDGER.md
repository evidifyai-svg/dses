# Claim ledger

**Applies to:** every statement this project makes outside the specification.
Pages, outreach, reports, talks, posts, papers, and messages.

`CLAIMS-CLASSIFICATION.md` governs what the specification asserts about itself
and is machine-checked against the verifier and the fixtures. This file governs
what a human says about the specification to someone else, where no checker is
watching. The two are different problems. A sentence can be true of the software
and still overclaim to a reader who does not know what was measured.

**The rule every entry serves:** no declarative sentence in outward-facing
material is stronger than the strongest mechanically established claim behind
it. Anything a reader is being asked to determine stays a question.

An entry has a claim, the wording that is allowed, and the extrapolation that is
not. The forbidden column is not a list of rude things to avoid. It is a list of
readings a reasonable person would take from a slightly stronger sentence.

---

## 1. Ordering

**Allowed.** The record establishes the order in which judgment was recorded
relative to AI exposure, under the stated trust assumptions.

**Forbidden.** That the record establishes what a person perceived, understood,
considered, or was influenced by. Presentation is not perception. An event says
an output was presented, never that it was read.

## 2. Integrity

**Allowed.** Internal integrity, meaning the supplied bytes are mutually
consistent with the chain presented. Historical integrity relative to a named
prior checkpoint, witness, or anchor, and only relative to one that is named.

**Forbidden.** Tamper-proof, immutable, unalterable, or any unqualified
"cannot be changed". Also forbidden: tamper-evident with no trust anchor named,
which is the same overclaim wearing a technical word.

## 3. Anchoring

**Allowed.** Anchoring narrows the operator-rewrite model to the anchored
portion, with coverage reported per chain.

**Forbidden.** That anchoring closes the operator-rewrite model. Unanchored
suffixes establish internal consistency only, and whether external anchoring
closes or merely narrows the model is an open question put to reviewers, not a
settled result to assert.

## 4. Independent implementation

**Allowed.** The current count of independent implementations, which is zero,
stated plainly and without softening.

**Forbidden.** Implying adoption, interest, pipeline, or momentum from
conversations, downloads, stars, traffic, or test counts. None of those is an
implementation. The fixed sentence for outreach stands: code written here would
only establish that Evidify can implement its own schema.

## 5. Review status

**Allowed.** The specification's own wording, that no human subject-matter
expert has reviewed it, for as long as that remains true. When attestations
exist, the reviewer, the lane, the version reviewed, and the disposition.

**Forbidden.** Naming a person who has been approached but has not attested.
Describing a conversation as a review. Describing a reviewer as endorsing,
supporting, or being involved with the project. A reviewer with a stake in the
outcome is not independent, so no reviewer is offered a role, a title, or
standing.

## 6. Conformance reports

**Allowed.** That a dated report was issued about named bundles, with its scope
and limitations reproduced.

**Forbidden.** Certified, accredited, approved, listed, or badged. That a report
covers an implementation as a whole rather than the bundles examined. That a
past report says anything about a later build.

## 7. Metrics

**Allowed.** That the reliance metrics are conditioned rates with declared
denominators, recomputed from committed evidence, reported with an interval and
with the reliance context that cannot be detached from them.

**Forbidden.** Reading any rate as a disposition, a competence, a standard of
care, or a trend. Comparing the two focal conditional rates against each other.
Reporting a point estimate without its interval and context. Presenting a rate
from a design whose structure the artifact itself discloses to be
repeated-measures as though it were independent trials.

## 8. Safety and outcomes

**Allowed.** That the record makes a decision sequence reconstructable, and that
reconstructability is a precondition for studying whether anything about the
sequence matters.

**Forbidden.** That DSES improves decisions, prevents errors, reduces harm, or
changes outcomes. None of that has been measured. Where insurance is in scope,
this sentence travels verbatim: "We make no claim that it reduces losses or
predicts claims."

## 9. Legal effect

**Allowed.** That the schema refuses eleven determination fields, and that
governance requirements are declared before an analysis runs. A DSES record
establishes that safeguards were declared.

**Forbidden.** Any statement about admissibility, discoverability, privilege,
legal sufficiency, or protection from liability. No DSES record establishes that
anyone honoured a declared safeguard. The schema creates no privilege and
defeats no lawful discovery.

## 10. Comparison with other work

**Allowed.** DSES's own published limits, stated in full. Relationships to
another published artifact expressed only as identical, narrower than, or
broader than, and only against that artifact's public text, cited.

**Forbidden.** Characterizing any other standard, product, or organization
beyond its own public text. Inferring what another project cannot do from what
it has not published. Competing on another project's chosen framing or borrowed
vocabulary. Where a comparison is made, the reader is pointed at the other
project's text rather than asked to take this one's summary of it.

## 11. Marks and patents

**Allowed.** DSES™ and EVIDIFY™ with TM. Trademark applications described as
pending.

**Forbidden.** The registered symbol before registration. Any patent marking,
whether a marking phrase, an application number, or a grant number. The
provisionals lapsed by choice, so there is nothing to mark.

---

## Using this file

Before anything goes out, read every declarative sentence against the entry it
falls under. The test is not whether the sentence is defensible. It is whether a
reader who believed it, and then read the specification, would find the
specification weaker than the sentence led them to expect.

If a sentence needs a footnote to survive that test, it is the wrong sentence.
