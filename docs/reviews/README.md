# Named expert reviews

Attestations from named human experts who reviewed a specific version of
this specification. Published verbatim, under the reviewer's name, in the
form the reviewer signed.

Nothing here is an endorsement or a certification. A reviewer states what
they read and what they concluded, including objections. A review with
objections is a completed review.

## What is in this directory

`<lane>-<surname>-<version>.md` for each attestation, where lane is
`statistics`, `protocol`, or `health-law`. Each file carries the version
reviewed and the archive digest the reviewer was given, so a reader can tell
exactly what text an attestation covers.

`dispositions-<version>.md` records what was done about each objection:
accepted with the change made, accepted with the change deferred and why, or
declined with the reason. Every disposition also appears in the
specification's changelog for the release that carries it. Reviewers see
their dispositions before publication and may append a response, which is
published with the same status as the original attestation.

## What review does and does not do here

Review does not replace the machine gate, and the gate does not replace
review. Every requirement marked implemented in `CLAIMS-CLASSIFICATION.md`
names a verifier rule and a regression fixture that asserts the rule fires,
and `scripts/release_lint.py` fails the build when that correspondence
breaks. What that machinery cannot establish is whether the requirements
are the right requirements, whether a claim is limited correctly, or whether
a statistic means what its name suggests. That is what the people named here
were asked about.

The specification discloses in its provenance section that its adversarial
review rounds were conducted by an AI system and that its reference
implementation was written by AI systems. Version 0.2.0 was minted on
October 18, 2026 with no completed attestation, and its provenance section
records that state lane by lane. An attestation received after the mint is
published here under the reviewer's name, with the version and archive
digest the reviewer was given; a disposition that changes published text is
handled as an erratum under `ERRATA-v0.2.md` or carried into 0.2.1. The
disclosure of AI involvement stays in the specification permanently either
way.

## Requesting a review

Reviewers are asked directly, given a scoped packet, and told which claim
rows fall in their lane. The current packet is
`docs/review/REVIEW-PACKET-v0.2.0-rc14.md`; earlier packets stay beside it as
the record of what their holders were sent. The packet covers rc14. Version
0.2.0 differs from rc14 only as recorded in
`docs/review/RC14-TO-0.2.0-DIFF.md`, and an attestation against rc14 is
accepted and published as an attestation of rc14. Anyone may also file findings
without being asked, through the repository's issues; unsolicited findings
are handled under `GOVERNANCE.md` and are not attestations.
