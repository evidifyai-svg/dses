# Named Expert Review: DSES v0.2.0-rc11

Prepared 2026-08-24 by Joshua M. Henderson, Ph.D., Evidify LLC.
For reviewers in three lanes: statistics, protocol and cryptography, health
law and clinical governance. One packet; your lane's scope is in the appendix
that names it. Expect two to six hours depending on lane.

## 1. What you are being asked to do

Read the parts of the Decision-Sequence Evidence Schema (DSES™) v0.2.0-rc11
that fall in your expertise, decide whether the claims there are correctly
stated and correctly limited, and put your name on a short attestation that
says what you reviewed and what you concluded, including objections.

You are not being asked to endorse DSES, to certify anything, or to say the
approach is a good idea. A filed objection with a published disposition
counts as a completed review. Praise without specifics does not.

## 2. Why a human review is the gate

The specification discloses, in its own provenance section, that every round
of adversarial review so far was conducted by an AI system and that the
reference implementation was written by one. It says no human subject-matter
expert has reviewed it. That sentence is a release blocker: the build tooling
refuses to mint a permanent 0.2.0 while it stands. The compensating design is
that claims are machine-checked rather than vouched for, but the author is
explicit that verifiability does not substitute for expert review.

Your review is the thing that lets that sentence be rewritten truthfully.

## 3. What DSES claims, in one paragraph

A DSES record establishes the order in which a human judgment was committed
relative to when that human was exposed to an AI output, and, in the v0.2
outcome layer, whether the resulting decision was correct under a criterion
the deployment prespecified before outcomes were known. It does this with a
hash chain, commit-then-reveal payload commitments, checkpointed Merkle roots,
signatures under a declared profile, and externally anchored timestamps whose
trust root the verifier takes from outside the package. What it does not do
is at least as important: it assigns no fault, establishes no standard of
care, creates no privilege, makes no admissibility claim, and does not
establish that any individual clinician is competent or negligent. Section
9.6 makes this a normative non-claim with eleven schema-invalid determination
fields. The claims table (CLAIMS-CLASSIFICATION.md) labels every requirement
by what kind of establishment is possible in principle (S, C, X, T, A) and
whether this build actually performs it (implemented, partial,
not_implemented, not applicable, out of scope).

## 4. Materials

Every link below is pinned to the tag `v0.2.0-rc11`, so the text you read is
the text you attest to. Do not read from the default branch; it moves.

- Specification (v0.2 outcome layer): https://github.com/evidifyai-svg/dses/blob/v0.2.0-rc11/DSES-v0.2.md
- Specification (v0.1 substrate, for context): https://github.com/evidifyai-svg/dses/blob/v0.2.0-rc11/DSES-v0.1.md
- Claims table: https://github.com/evidifyai-svg/dses/blob/v0.2.0-rc11/CLAIMS-CLASSIFICATION.md
- Conformance policy: https://github.com/evidifyai-svg/dses/blob/v0.2.0-rc11/CONFORMANCE-POLICY.md
- Governance: https://github.com/evidifyai-svg/dses/blob/v0.2.0-rc11/GOVERNANCE.md
- Scorecard (what is not established): https://github.com/evidifyai-svg/dses/blob/v0.2.0-rc11/SCORECARD.md
- Release notes for this candidate: https://github.com/evidifyai-svg/dses/blob/v0.2.0-rc11/docs/RELEASE-NOTES-v0.2.0-rc11.md
- Signed archive: https://github.com/evidifyai-svg/dses/releases/tag/v0.2.0-rc11,
  file `dses-v0.2.0-rc11-publication.zip`,
  sha256 75d7d5f55eeed412571047f9e650ea9b806f7f34aecaf023f5938895edb89233

Read the specification sections named in your appendix, then the matching
rows of the claims table. Claim rows are linkable by line: append
`?plain=1#L53` to the claims-table URL to land on row 3.4f, for example.
- Run it yourself if you want to (optional, ten minutes, Python 3.12+):

```
git clone https://github.com/evidifyai-svg/dses.git && cd dses
git checkout v0.2.0-rc11   # the tag, not main
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
bash run_all.sh
```

Expected: release lint 0 problems, 206 objects, 2205 checks 0 failures, OL
CONFORMANT, 158 adversarial cases rejected at the asserted rule, ALL GREEN.
The point of the offer is that you never have to take the author's word for
a number in this packet.

## 5. What we do with your review

- Your attestation is published verbatim in docs/reviews/ in the repository
  under your name, with the date and the exact version and archive hash you
  reviewed.
- Each objection gets a written disposition in the next release candidate's
  changelog: accepted with the change made, accepted with the change
  deferred and why, or declined with the reason. You see the disposition
  before it is published and may append a response.
- SCORECARD.md moves the "named external expert reviewers" count.
- The specification's provenance section is rewritten to name you as a
  reviewer of the stated scope. It will not say you approved anything you
  did not.

## 6. What we will not do

- Describe your review as an endorsement, certification, or approval.
- Use your name or institution in marketing copy.
- Edit your attestation. If you want to change it, you resubmit it.
- Send you a revised draft and treat silence as acceptance.

## 7. Compensation and conflicts

State any relationship with Evidify LLC or the author in the attestation.
[Josh: decide and state here whether there is an honorarium. If none, say so
plainly. If the reviewer is a collaborator on HB-LIVER or a co-author, say
that the attestation will carry that disclosure.]

---

## Appendix A. Statistics lane

Sections: 6.11 (adjudication and agreement), 8 (reliance metrics: RAIR, RSR,
EAR; intervals; design structure; panel-scope chance-corrected agreement),
9.5, Annex C entries rc9 through rc11 for the independence-violation history.

Claim rows: 6.11g, 6.11h, every 8.x row, 8.12 (T + A), 9.5 (T / A), 9.3d
(minimum cell size and interval), 9.3p (case-mix adjustment adequacy is A).

Questions we most want answered:

1. Percent agreement is declared as the item-scope floor and Fleiss kappa is
   panel-scope only, because kappa over a single item is 0/0 (shipped case
   c00, two concordant assessors). Is that scoping correct, and is the
   marginal-distribution estimation over the panel stated correctly?
2. `design_structure` disclosure (MET-DESIGN) exists to expose repeated
   measures on one case. Does the disclosure carry what a reader needs to
   judge a design effect, or does it invite a false sense of independence?
3. The binomial point and interval rule (binomial-point-v1) is the only
   estimator shipped. Is its use as a default defensible for RAIR/RSR/EAR
   given that the units are decision instances, not independent trials?
4. Section 8.12 says interval independence assumptions and exclusion
   informativeness are stated but not mechanically established. Is anything
   in Section 8 phrased as if it were established when it is not?
5. Is there any metric whose name suggests a causal claim the definition does
   not support?

## Appendix B. Protocol and cryptography lane

Sections: 3.1 through 3.8 (hashing, commitments, checkpoints, anchoring,
signatures, executable rules), 5.2 and 5.3 (membership manifests, inclusion
and consistency proofs, snapshot recomputation), 6.3 (v0.1 replay), 2 (threat
model, A1 operator rewrite and A2 ingestion timing), 3.4f.

Claim rows: every row whose verification class contains C; 3.4a, 3.4b
(not_implemented RFC 3161), 3.4f (partial), 3.5, 3.6a-3.6i, 3.8a-3.8h, 5.1a,
5.2c, 5.2e, 5.3a, 5.3b, 6.3b-6.3d, 2.2a, 7.3c (not_implemented).

Questions we most want answered:

1. The trust root for anchors is external by design: a verifier that
   resolved the anchor authority's key from inside the package would prove
   only that a key the package nominates signed the receipt. Is the A1 threat
   model complete, and does DSES-ANCHOR-v1 (signed receipt over artifact
   hash, anchor time, authority identity) close it or merely narrow it?
2. Commit-then-reveal: content commitment plus hiding commitment under a
   nonce, nonce store as a sidecar. Is there a reveal-ordering or
   nonce-reuse attack the adversarial suite does not model?
3. RFC 9162 consistency proofs between checkpoint epochs, with inline head
   observations below a threshold and inclusion proofs above it. Is the
   threshold switch itself a place where an operator can choose the weaker
   path?
4. DSES-SIG-v1 statement encoding is fixed by shipped test vectors. Is the
   context binding sufficient to prevent cross-object signature reuse
   (SIG-TARGET)?
5. Executable rules are content-addressed by digest of the module bytes with
   an explicit locator, and the verifier executes them. Is executing
   package-supplied code inside the verifier an acceptable design when the
   package is operator-rewritable, given that the digests are what is
   checked?
6. Claim 3.4f: the verifier derives "externally anchored before cutoff" as a
   boolean and does not report the grade labels the prose names. Should the
   grade vocabulary be removed from the spec, or should the verifier report
   it? Either answer is fine; the current state is disclosed as partial.

## Appendix C. Health law and clinical governance lane

Sections: 9 in full (9.1 privilege, 9.2 disposition, 9.3 unit of analysis
and individual-level derivation, 9.4 declared purpose, 9.5, 9.6 sequence is
not fault), 13 (what this layer does not claim), Annex E (reconstruction
questions), CONFORMANCE-POLICY.md "What conformance does not assert",
RELIANCE-CONTEXT-EXAMPLE.md, GOVERNANCE.md.

Claim rows: 9.1, 9.2, 9.3a-9.3r, 9.4, 9.4b, 9.5, 9.6, and every row whose
verification class contains A.

Read this first: DSES asserts no legal conclusion. It records the factual
sequence of a human judgment relative to an AI exposure. The question for
this lane is not whether that record would be admissible, privileged, or
dispositive; the spec says those are external. The question is whether the
spec's non-claims are stated tightly enough that an implementer, a plaintiff,
a defendant, or a regulator could not honestly read a DSES record as
asserting more than it does.

Questions we most want answered:

1. Section 9.6 lists eleven determination fields that are schema-invalid
   (negligence, causation, liability assignment, admissibility, and so on).
   Is the list complete? What is missing that a litigant would reach for?
2. Section 9.3 restricts individual-level metrics to deployments that
   anchored a secondary-use governance artifact declaring purpose, minimum
   cell size, bounded window, balanced reliance context, notice and access,
   and appeal. Does that governance floor read as adequate for a peer-review
   or credentialing use, or does it create a record that will be used for
   adverse action regardless of what the artifact says?
3. 9.3r: pseudonymous subject binding does not establish civil identity.
   Does the pseudonymity hold up against discovery in practice, and if not,
   is the spec's disclosure of that limit adequate?
4. 9.1: no privilege determination field, and 9.3k says discoverability,
   privilege, and legal usability are out of scope. Is "out of scope"
   the right disposition, or should the spec say more about the fact that a
   DSES record is likely discoverable and design accordingly?
5. The conformance policy says "DSES Conformant" means passing a published
   gate and filing a transcript, and lists what it does not assert. Is there
   any reading of "conformant" that a reasonable clinician, hospital counsel,
   or carrier would take as a safety or quality representation?
6. CONFORMANCE-POLICY.md and RELIANCE-CONTEXT-EXAMPLE.md: is the insurance
   language limited correctly? Evidify operates under a standing rule that
   the only permitted sentence in an insurance context is a disclaimer of
   the two claims a carrier would most want made. Read the policy text and
   tell me whether the surrounding material lives up to it.

---

## Attestation (please return as a signed PDF or a signed commit)

```
DSES NAMED EXPERT REVIEW ATTESTATION

Reviewer:            [name, credentials]
Affiliation:         [institution; "independent" if none]
Lane:                [statistics | protocol and cryptography | health law and clinical governance]
Version reviewed:    DSES v0.2.0-rc11
Archive sha256:      75d7d5f55eeed412571047f9e650ea9b806f7f34aecaf023f5938895edb89233
Sections reviewed:   [list]
Claim rows reviewed: [list]
Gate re-run:         [yes, environment; | no]
Time spent:          [hours]

Conclusion (choose one):
  [ ] The claims in my scope are correctly stated and correctly limited as of this version.
  [ ] The claims in my scope are correctly stated and limited subject to the objections below.
  [ ] I identified a defect in my scope that I consider release-blocking (stated below).

Objections and findings (numbered; cite section and claim row):
  1.
  2.

Relationship to Evidify LLC or the author:
  [none | collaborator on ... | co-author of ... | honorarium received: ...]

I understand this attestation will be published verbatim under my name, that
it is not an endorsement or certification, and that objections receive a
written disposition I may respond to before publication.

Signature:           ____________________    Date: ____________
```
