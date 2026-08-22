# DSES Conformance Policy

Version 1.0, August 2026. This policy governs use of the phrase "DSES
Conformant" and equivalents.

## Anyone may implement

The specification is CC BY 4.0 and the reference code is MIT. No permission,
fee, or notification is required to implement DSES, in whole or in part, in
any language, for any purpose.

## Vocabulary

Two tiers exist today. **DSES-compatible** is self-declared (see
TRADEMARKS.md) and free of any process. **DSES Conformant** requires the
evidence below. Certification tiers involving independent assessment are
reserved for the future and are not currently offered by anyone.

## Claiming "DSES Conformant" requires evidence

An implementation, deployment, or evidence package may be described as "DSES
Conformant" only when both of the following hold:

1. It passes the published verification gate for a named specification
   version: the reference verifier (or an implementation demonstrably
   equivalent on the published test vectors and adversarial fixtures) reports
   conformance with zero failures.
2. A verification transcript has been submitted to the conformance registry
   maintained by Evidify LLC: the gate output, the specification version and
   archive hash verified against, and the environment record (OS, runtime,
   pinned dependency versions).

Registry listing is free. The registry exists so that a conformance claim is
always checkable by a third party against a named transcript, which is the
same standard the specification applies to its own claims.

## What conformance does not assert

Conformance is a statement about evidence structure and verifiability. It is
not an endorsement of a product, not a statement about clinical performance,
and not a legal determination of any kind. Consistent with Section 9 of the
specification, no conformant artifact may assert a standard-of-care,
reasonable-use, competence, or negligence determination, and a conformance
claim may not be presented as implying one.

## Partial and derived use

Implementations covering only the v0.1 sequence layer, or only the v0.2
outcome layer, must scope the claim ("DSES v0.1 Conformant, sequence layer").
Unverified or modified derivations must not use the mark and should be
described as "based on DSES."

## Enforcement

"DSES" is claimed as a trademark of Joshua M. Henderson / Evidify LLC.
Conformance claims that do not meet this policy will be requested to correct
or remove the claim; the registry is the authoritative public record either
way.

Contact: conformance@evidify.ai
