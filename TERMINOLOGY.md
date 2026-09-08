# Terminology

**Applies to:** DSES v0.2 and every document, page, report and message that
describes it.

This is a file, not a registry. It fixes the meaning of prose terms so the same
word means one thing in the specification, on the public pages, in outreach, and
in a conformance report. It does not define schema vocabulary: machine-readable
identifiers live in the schemas and are checked by
`scripts/check_vocabulary.py`. What is written here is the part no checker can
police, which is exactly why it needs to be written down.

An entry records a ruling. Changing an entry is a decision with a date, not an
edit.

## The name

The Decision-Sequence Evidence Schema (DSES™) is a **schema**. It is not a
standard body's standard, and it is never expanded as "Decision Sequence
Evidence Standard". That expansion appeared in five outreach drafts before it
was caught, which is the reason this entry is first.

First reference in any document is the full name with the mark. Subsequent
references are adjective plus noun: a DSES record, a DSES package, DSES
vocabulary. The bare acronym is not used as the subject of a sentence.

On the specification site the artifact is called a specification. On the company
site it is called a standard, in the ordinary-English sense of an agreed way of
doing something. Both are accurate for their audience and neither migrates.

## Integrity

**Internal integrity.** The bytes supplied are mutually consistent with the
chain presented. This is what a verifier establishes from a package alone.

**Historical integrity.** The bytes supplied are the same bytes that existed at
the time. This is **not** establishable from an operator-held package. An
operator who controls the whole history can alter an event, recompute every
downstream hash, and present a second internally consistent chain. Establishing
historical integrity requires a trust anchor outside the operator.

The verdict line is "internally conformant, historical integrity
unestablished", and it is never shortened.

**Permitted of a record:** committed, hash-bound, finalized, internally
consistent.

**Not used of a record:** sealed, tamper-proof, immutable, unalterable. Each
asserts historical integrity that the mechanism does not deliver.

## Sequence and fault

DSES records the factual sequence in which judgment formed relative to AI
exposure. It assigns no fault. The specification states this as a normative
non-claim and the schema refuses eleven determination fields outright rather
than discouraging them.

The direction of inference is unconstrained by construction. The record that
appears to expose a professional who resisted useful AI is the same record
documenting every occasion on which resisting it was right. A conformant package
is not a defence either.

## Reference distribution and threshold

A reference distribution is descriptive. It becomes a threshold only if an
external authority separately adopts it as one. Nothing in this project turns a
distribution into a norm, and no document describes one as expected, acceptable,
or within range.

## Candidate and release

A candidate carries an `-rcN` suffix, may circulate for comment, and may have
open review provenance. A release carries no suffix and may not. Identifiers can
rename between candidates; they do not rename after a release. Outreach that
points at a candidate says so, and says that a rename will come with a diff.

## Conformance

**Conformance report.** A dated written document about specific bundles from a
specific implementation, naming its scope, its limitations, and a signer. It is
the only thing this project issues about someone else's implementation.

**Not issued, and not to be implied:** certification, accreditation, a badge, a
seal, a listing, a directory entry, or approval. A report is a document. It is
never a status a reader carries around.

**DSES-compatible** and **DSES Conformant** are protected conformance
vocabulary with normative meaning and are not used loosely.

**Independent implementation** means an emitter written by someone else from the
published documents. Code written here is not one, at any volume. The count is
published and is currently zero.

## Attestation and verification

**Verified** describes something a checker recomputed.

**Attested** describes something a person asserted and no checker can reach.
The specification lists its attested requirements explicitly so the two are
never blurred.

A named reviewer's written finding is an **attestation**. It is published as
received, including when it is an objection.

## Marks and status

DSES™ and EVIDIFY™ carry TM. The registered symbol is not used, because neither
mark is registered. Applications are pending and are described as pending.

No patent marking of any kind appears in any document or page: no marking
phrase, no application number, no grant number. The provisionals were allowed to
lapse by choice, so there is nothing to mark.

## Insurance

Where insurance is discussed at all, this sentence travels verbatim:

> We make no claim that it reduces losses or predicts claims.

The two claims that sentence disclaims are not made anywhere, not implied, and
not softened into hedged versions of themselves. The guard holds the exact
wording, and that sentence is the only place the phrases may appear.

## Credential

Joshua M. Henderson, Ph.D. The credential is written Ph.D. and no other
abbreviation is used anywhere.
