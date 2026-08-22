# Security Policy

DSES is an evidence specification. A soundness defect here is not a bug, it is
the product failing at the only thing it claims to do, so reports are treated
accordingly.

## Reporting

Email security@evidify.ai. Include the spec version or commit, a description,
and if possible a reproducing package or fixture. You will get an
acknowledgment within 72 hours and a substantive response within 14 days.

## Scope

In scope: anything that lets a package verify when it should not, or fail to
verify when it should. Forged ordering, hash or signature preimage ambiguity,
canonicalization divergence, verifier rules that can be satisfied vacuously,
fixtures that pass for the wrong reason, denominator or context manipulation
that the verifier accepts.

Out of scope: attacks requiring control of the external trust root, and
downstream misuse of truthfully verified evidence (governed by Section 9.3,
not by this policy).

## Disclosure

Confirmed soundness defects are disclosed in the changelog with a regression
fixture, named plainly, and credited to the reporter unless anonymity is
requested. This project has already published its own defects, including a
forged-row incident preserved permanently in its audit chain; reporters will
not be met with minimization.
