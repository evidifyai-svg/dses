# Interoperability report: [producer] records read by [consumer]

- Kind: interoperability report
- Date:
- DSES version and archive SHA-256:
- Producer implementation (wrote the records) and registry slug:
- Consumer implementation (read or verified the records) and registry slug:
- Author of this report and affiliation:
- Evidence package location and SHA-256:

An interoperability report records what happened when records written by one
implementation were read or verified by a different one. Agreement and
disagreement are both results. The report is not a conformance statement for
either side.

## 1. What was exchanged

The package or sequences, how many, their data class (synthetic, deidentified,
or locally reproducible), and the digest of each.

## 2. Procedure

The exact commands, in order, with versions. A reader should be able to rerun
them from this section alone.

## 3. Results

| Check or rule | Producer's own verifier | Consumer | Agree |
|---|---|---|---|
| | | | |

State totals: checks run, checks agreed, checks disagreed, checks one side
could not evaluate.

## 4. Disagreements

For each one: the bytes involved, what each side concluded, and the cause if
known. Classify the cause as one of: producer defect, consumer defect,
specification ambiguity, specification defect, or unresolved.

## 5. Specification findings

Anything that should become an erratum, a fixture, or a clarification, with
the section number. A finding that names a concrete counterexample can be
filed under `CONTRIBUTING.md`.

## 6. Independence statement

Who wrote each implementation, what code they share, and any relationship
between the two teams or between either team and Evidify LLC, stated so that a
reader can judge for themselves.

## 7. Limitations

What this exchange did not test.
