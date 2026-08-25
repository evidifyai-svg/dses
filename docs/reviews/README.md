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
review rounds were conducted by AI systems and that its reference
implementation was written by one. The build tooling refuses to mint a
non-candidate version while that disclosure stands unresolved. These
attestations are how it gets resolved, and the disclosure of AI involvement
stays in the specification permanently either way.

## Requesting a review

Reviewers are asked directly, given a scoped packet, and told which claim
rows fall in their lane. The current packet is
`docs/review/REVIEW-PACKET-v0.2.0-rc11.md`. Anyone may also file findings
without being asked, through the repository's issues; unsolicited findings
are handled under `GOVERNANCE.md` and are not attestations.
