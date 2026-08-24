# Contributing to DSES

Contributions are welcome, and the bar is deliberately explicit.

## The architecture is frozen

The core evidence architecture (event model, hash chaining, canonicalization,
commitment and signature profiles, Merkle and anchoring semantics, snapshot
recomputation) is frozen. A finding against a frozen component requires one
of: a concrete counterexample (a package or fixture demonstrating the
defect), an internal contradiction in the specification text, or a
demonstrated interoperability failure between conforming implementations.
Style preferences, alternative designs, and "this could also work" proposals
are welcome as discussion but do not reopen frozen components.

## Findings require fixtures

This specification's rule for itself applies to contributions: a claimed
defect is "implemented" as a finding only when it ships with a regression
fixture that fails before the fix and passes after. PRs that change verifier
behavior must add or update fixtures; the release lint enforces this and CI
runs the full gate on every push.

## What is especially valuable

Adversarial packages that verify but should not. Ambiguity reports from
independent implementation attempts (say what you had to guess). Statistical
review of the estimator and interval choices. Legal and governance review of
Section 9.3 against real institutional practice. Domain mappings beyond
radiology.

## Process

Open an issue before large changes. Small fixes can go straight to PR against
a feature branch, never main. Every PR must leave `bash run_all.sh` fully
green. By contributing you agree your contributions are licensed under the
repository's licenses (CC BY 4.0 for specification text, MIT for code).

## Conduct

Direct technical criticism is the point of this project. Criticize claims,
not people, and bring evidence.
