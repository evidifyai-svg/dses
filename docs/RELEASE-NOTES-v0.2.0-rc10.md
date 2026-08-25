# DSES v0.2.0-rc10 release notes

Release candidate. Permanent identifiers remain unminted pending named human
expert review.

## What rc10 is

The DSES™ specification (Decision-Sequence Evidence Schema) is an open
specification stewarded by Evidify LLC under CC BY 4.0 for the specification
text and MIT for the code. Release candidate 10 of the v0.2.0 outcome layer is
the first publication tree that carries the external implementation surface:
`IMPLEMENT.md`, `IMPLEMENTATION-CHECKLIST.md`, `FOUNDING-IMPLEMENTERS.md`, and
the `quickstart/` directory with runnable Python and TypeScript examples.

## Publication archive

    file      dses-v0.2.0-rc10-publication.zip
    members   102
    manifest  101 entries, all verified
    sha256    3721c4777b5a5fc3212de43a56801112ba1f38f22a336f05fb4e8cd47c878bfc

Built from the `feat/v0.2-outcome-layer` tree at commit `0a5e12b`, whose file
tree is identical to `main` at `987031b`, which is what this tag points at.

## Archive digest supersession

Two digests have circulated for rc10. One version label gets one archive hash,
so both earlier values are recorded here rather than quietly dropped.

- `48b88fe05f53139c21752c00e9986702031fce0801da03851f340e884722d8b6` was built
  from commit `306d925`, before the external implementation kit merged. It is a
  correct digest of a tree that is not the rc10 publication tree. It was
  reproduced in four environments, and that reproduction stands as a statement
  about `306d925`, not about rc10.
- `3721c4777b5a5fc3212de43a56801112ba1f38f22a336f05fb4e8cd47c878bfc` was
  reported earlier without a recorded verification.

The second value is confirmed and is the digest of this release. It was rebuilt
from a clean clone of the public repository in a Linux container, rebuilt again
in the same environment to confirm the build is deterministic for a fixed source
tree, extracted to a temporary directory, checked entry by entry against
`RELEASE-MANIFEST.sha256` with all 101 entries reporting OK, and re-run through
the full release gate from the extracted copy. It was then reproduced independently on macOS arm64 from a
separate clone, producing the identical digest.

Any prior reference to `48b88fe0` as the rc10 archive digest is superseded.

Reproduced again on 2026-08-24 from a fresh clone of the public repository in a
new Linux container on Python 3.11.15 with the pinned dependencies, at
`0a5e12b`, whose tree object `e093e921` is byte-identical to the tree at
`main` `987031b`. The rebuild produced the same digest, 102 members, and the
manifest verified 101 of 101. The full gate was then run a second time from the
extracted archive rather than from the repository, and reported the same counts
as the table below. That is a fourth verification path, and it is the reason
`3721c477` is now recorded as confirmed rather than reported.

## Gate result at the publication tree

    RFC 8785 canonicalization self-test    6 vectors passed
    release lint                           148 requirement rows,
                                           116 verifier rules,
                                           116 rule-asserting fixtures,
                                           0 problems
    schema validation                      206 objects, 0 errors
    reference verifier                     2,286 checks, 0 failures
    outcome layer                          OL CONFORMANT
    adversarial suite                      158 cases, 158 rejected at the
                                           asserted rule, 0 not
    external quickstart                    2 valid examples passed,
                                           6 targeted mutations rejected
    regeneration in a temporary tree       206 objects, 0 errors

Public-copy guards, run from the repository root:

    language guard v2                      4 files scanned, 0 errors, 0 warnings
                                           self-test 45 passed, 0 failed
    seo guard                              2 files scanned, 0 errors, 0 warnings
                                           self-test 46 passed, 0 failed

## What this result does not establish

Passing the bundled gate does not establish an independent implementation. The
gate runs the reference code against artifacts the reference code produced. The
recomputation step calls the same orchestration the generator called, over the
same rule modules and the same canonicalization, which establishes that the
declared rules reproduce the registered counts and nothing more. See claim 7.3c.

No conformance is asserted and no certification is offered. The quickstart tests
make no conformance claim. The scorecard continues to report independent
implementations at zero.

An implementation counts only when an external party has written its own emitter
and the public verifier accepts the artifact it produced. Evidify answers
questions, reviews output, and fixes specification ambiguities that implementers
surface. Evidify does not write an implementer's emitter code.

## Liability direction

The DSES specification records the order of a committed human judgment relative
to specified AI exposure. Sequence is not fault. The specification carries this as a normative
non-claim, the schemas admit no liability-assignment or negligence-determination
field on a derived metric, and the adversarial suite rejects derived artifacts
that assign liability to a professional or assert that AI exposure caused an
outcome.

## Known documentation gap in this candidate

`ENVIRONMENTS.md` ships counts from an earlier candidate: 199 objects, 2027
checks, 113 adversarial cases, 68 manifest hashes. The current gate reports 206,
2,286, 158, and 101. The file also predates the two environments that reproduced
this archive. Correcting it changes the bytes of the publication archive and
therefore its digest, so it is deferred to the next candidate rather than
re-cutting a digest that has already been reproduced and published. This note is
the correction of record until then.

Joshua M. Henderson, Ph.D.
Evidify LLC
