# rc14 to 0.2.0: what changed for a reviewer holding the rc14 packet

Prepared 2026-10-18 by Joshua M. Henderson, Ph.D., Evidify LLC. For the
reviewers who were sent `REVIEW-PACKET-v0.2.0-rc14.md` on 2026-10-11 and
told that the identifiers would rename at 0.2.0 with the diff handed over.
This is that diff.

## The one-paragraph version

Nothing you were asked to review changed. No requirement, rule, schema
structure, fixture, or verifier line moved between rc14 and 0.2.0. The
label `0.2.0-rc14` became `0.2.0` everywhere it appeared, the schema `$id`
URLs moved from `/0.2.0-rc14/` to `/0.2.0/`, the worked example was
regenerated once for the new label (fresh keys, fresh hashes, same
structure and verdicts), and five pieces of prose that described the
document as a candidate now describe it as a release. One of those five is
the provenance section at the end of `DSES-v0.2.md`, which now records that
no named human review completed before the mint, including yours. Your
attestation, if you file one, is published in `docs/reviews/` under your
name against the version and digest you reviewed, exactly as the packet
said, and any objection is dispositioned in an erratum or in 0.2.1.

Attest to rc14 if that is what you read. The packet said so and it still
holds: `v0.2.0-rc14` is a tag that does not move, and the text at that tag
is the text 0.2.0 was minted from.

## Gate signature

Unchanged: lint 0 problems, 206 objects, 2205 checks, OL CONFORMANT, 158
rule-asserting cases rejected at the asserted rule, 1 boundary fixture
held, quickstart 2 valid examples and 6 mutations rejected, vocabulary 833
terms and 0 findings, language guard 112 files 0 errors 37 warnings,
release manifest 109 entries, archive 110 members.

## Identifier and label changes

The schemas, scripts, tests, `run_all.sh`, `requirements.txt`,
`IMPLEMENT.md`, `CLAIMS-CLASSIFICATION.md`, `CITATION.cff` and
`.zenodo.json`. Every hunk is a label rewrite except three that are
plainly prose: the `CLAIMS-CLASSIFICATION.md` status line, the
`CITATION.cff` release date, and one sentence in the `.zenodo.json`
description that states the review counts at mint.

```diff
diff --git a/.zenodo.json b/.zenodo.json
index fb43618..a9fffa3 100644
--- a/.zenodo.json
+++ b/.zenodo.json
@@ -1,8 +1,8 @@
 {
   "title": "DSES: Decision-Sequence Evidence Schema",
   "upload_type": "software",
-  "version": "0.2.0-rc14",
-  "description": "Open specification for reconstructable human-AI decision evidence. The v0.1 sequence layer defines event, exposure, information-state, capture-level, and integrity vocabularies; an I2 single export establishes internal consistency only unless compared with a separately held checkpoint or supported by verified external anchoring. The v0.2.0-rc14 outcome layer adds denominator-closed eligibility manifests, outcome linkage, pre-consensus adjudication under declared charters, content-addressed executable rules, recomputable reliance metrics (RAIR, RSR, EAR), and governance constraints on unit of analysis and individual-level derivation. The shipped candidate supplies RFC 8785 commitments, signatures, RFC 9162 proofs, reader-supplied external anchor trust, release lint, an adversarial suite, and a reference verifier, with unimplemented and attestation-only claims named explicitly. Specification text is licensed CC BY 4.0 (LICENSE-SPEC.md); reference code is licensed MIT (LICENSE-CODE.md).",
+  "version": "0.2.0",
+  "description": "Open specification for reconstructable human-AI decision evidence. The v0.1 sequence layer defines event, exposure, information-state, capture-level, and integrity vocabularies; an I2 single export establishes internal consistency only unless compared with a separately held checkpoint or supported by verified external anchoring. The v0.2.0 outcome layer adds denominator-closed eligibility manifests, outcome linkage, pre-consensus adjudication under declared charters, content-addressed executable rules, recomputable reliance metrics (RAIR, RSR, EAR), and governance constraints on unit of analysis and individual-level derivation. The v0.2.0 release (minted 2026-10-18 from candidate rc14, with zero completed named human expert reviews and zero independent implementations, as its provenance section records) supplies RFC 8785 commitments, signatures, RFC 9162 proofs, reader-supplied external anchor trust, release lint, an adversarial suite, and a reference verifier, with unimplemented and attestation-only claims named explicitly. Specification text is licensed CC BY 4.0 (LICENSE-SPEC.md); reference code is licensed MIT (LICENSE-CODE.md).",
   "license": "cc-by-4.0",
   "creators": [
     {
diff --git a/CITATION.cff b/CITATION.cff
index 787caee..33ce902 100644
--- a/CITATION.cff
+++ b/CITATION.cff
@@ -2,8 +2,8 @@ cff-version: 1.2.0
 message: "If you use or cite DSES, please cite it as below."
 title: "DSES: Decision-Sequence Evidence Schema"
 type: software
-version: 0.2.0-rc14
-date-released: 2026-08-23
+version: 0.2.0
+date-released: 2026-10-18
 authors:
   - family-names: Henderson
     given-names: Joshua M.
diff --git a/CLAIMS-CLASSIFICATION.md b/CLAIMS-CLASSIFICATION.md
index 5587660..5bde70a 100644
--- a/CLAIMS-CLASSIFICATION.md
+++ b/CLAIMS-CLASSIFICATION.md
@@ -1,6 +1,6 @@
 # CLAIMS-CLASSIFICATION
 
-**Applies to:** DSES v0.2.0-rc14 (Release candidate for public comment)
+**Applies to:** DSES v0.2.0 (minted October 18, 2026)
 **Status:** Normative companion to Annex D. Release-blocking: no requirement ships unclassified.
 
 Two independent dimensions, kept separate because conflating them is itself a form of overclaiming.
diff --git a/IMPLEMENT.md b/IMPLEMENT.md
index fb3f9ac..c110915 100644
--- a/IMPLEMENT.md
+++ b/IMPLEMENT.md
@@ -12,7 +12,7 @@ records retroactively stronger.
 | Was an AI result actually presented to this actor, when, and in what form? | L1/I1 passive exposure logging | Operator-attributable application records of availability, presentation, exposure class, and final disposition | Tamper evidence, a pre-AI judgment, or independence |
 | What state was committed before exposure, and what changed afterward? | L2/I2 decision trajectory | Payload commitments and hash-chain internal consistency for a pre-exposure, exposure, revision, and final sequence | Historical immutability without a separately held checkpoint; enforced withholding; causation |
 | Could the specified AI output have appeared before the commitment? | L3/I3 only after workflow-specific review | The property supported by the deployed fail-closed enforcement mechanism and any separately verifiable anchor | Cognition, decision quality, negligence, or clinical benefit |
-| Was the decision correct under a prespecified criterion? | v0.2.0-rc14 outcome layer | Recomputable linkage, adjudication, denominator, and metric claims that the reference verifier implements | Truth beyond the declared criterion, statistical adequacy beyond the stated design, or legal conclusions |
+| Was the decision correct under a prespecified criterion? | v0.2.0 outcome layer | Recomputable linkage, adjudication, denominator, and metric claims that the reference verifier implements | Truth beyond the declared criterion, statistical adequacy beyond the stated design, or legal conclusions |
 
 L1 is the default production entry point. L3 is not a universal upgrade. In a
 clinical production workflow, changing when a device output appears requires
diff --git a/requirements.txt b/requirements.txt
index bae612c..60d0150 100644
--- a/requirements.txt
+++ b/requirements.txt
@@ -1,4 +1,4 @@
-# DSES v0.2.0-rc14 reference implementation dependencies.
+# DSES v0.2.0 reference implementation dependencies.
 # Python 3.11 or later.
 jcs==0.2.1
 jsonschema==4.26.0
diff --git a/run_all.sh b/run_all.sh
index 02dc62e..d7343c2 100755
--- a/run_all.sh
+++ b/run_all.sh
@@ -1,5 +1,5 @@
 #!/usr/bin/env bash
-# DSES v0.2.0-rc14 release gate.
+# DSES v0.2.0 release gate.
 #
 # Verify the shipped bytes first. Regeneration happens only afterward in an
 # isolated temporary copy, so a broken shipped artifact cannot be overwritten
diff --git a/schemas/dses-v0.2-definitions.schema.json b/schemas/dses-v0.2-definitions.schema.json
index 04cde11..d4d13f8 100644
--- a/schemas/dses-v0.2-definitions.schema.json
+++ b/schemas/dses-v0.2-definitions.schema.json
@@ -1,7 +1,7 @@
 {
   "$schema": "https://json-schema.org/draft/2020-12/schema",
-  "$id": "https://evidify.ai/schemas/dses/0.2.0-rc14/definitions.schema.json",
-  "title": "DSES v0.2.0-rc14 Definition Artifacts",
+  "$id": "https://evidify.ai/schemas/dses/0.2.0/definitions.schema.json",
+  "title": "DSES v0.2.0 Definition Artifacts",
   "description": "Six immutable, content-addressed definition artifacts. content_hash preimage: RFC 8785 canonical form with content_hash removed. Anchor evidence is PROHIBITED inside an artifact (it lives in anchor_evidence_recorded events), so timing evidence can improve without changing artifact identity. Prespecification is declared against an external cutoff, never against DSES ingestion order.",
   "oneOf": [
     {
diff --git a/schemas/dses-v0.2-derived.schema.json b/schemas/dses-v0.2-derived.schema.json
index bc1222b..48813e3 100644
--- a/schemas/dses-v0.2-derived.schema.json
+++ b/schemas/dses-v0.2-derived.schema.json
@@ -1,7 +1,7 @@
 {
   "$schema": "https://json-schema.org/draft/2020-12/schema",
-  "$id": "https://evidify.ai/schemas/dses/0.2.0-rc14/derived.schema.json",
-  "title": "DSES v0.2.0-rc14 Derived Analytic Artifacts",
+  "$id": "https://evidify.ai/schemas/dses/0.2.0/derived.schema.json",
+  "title": "DSES v0.2.0 Derived Analytic Artifacts",
   "description": "Immutable derived artifacts. They carry NO lifecycle field: effective status is replayed from derived_artifact_registered, derived_artifact_superseded, and derived_artifact_invalidated events on the cohort chain (Section 7.1). Singletons carry an assurance vector; aggregates carry inclusion filters and do not collapse heterogeneous assurance into a single vector.",
   "oneOf": [
     {
diff --git a/schemas/dses-v0.2-nonce-sidecar.schema.json b/schemas/dses-v0.2-nonce-sidecar.schema.json
index 46be722..214c96d 100644
--- a/schemas/dses-v0.2-nonce-sidecar.schema.json
+++ b/schemas/dses-v0.2-nonce-sidecar.schema.json
@@ -1,7 +1,7 @@
 {
   "$schema": "https://json-schema.org/draft/2020-12/schema",
-  "$id": "https://evidify.ai/schemas/dses/0.2.0-rc14/nonce-sidecar.schema.json",
-  "title": "DSES v0.2.0-rc14 Nonce Sidecar",
+  "$id": "https://evidify.ai/schemas/dses/0.2.0/nonce-sidecar.schema.json",
+  "title": "DSES v0.2.0 Nonce Sidecar",
   "description": "Nonces for randomized hiding commitments. Keyed by EVENT HASH, not event_id: event identifiers are unique only within a chain, so an id-keyed sidecar cannot unambiguously represent two events sharing an id across chains. The event hash is already a cryptographic identity and commits to the payload commitment.",
   "type": "object",
   "required": [
diff --git a/schemas/dses-v0.2-outcome-events.schema.json b/schemas/dses-v0.2-outcome-events.schema.json
index 15b80d6..4fe76b9 100644
--- a/schemas/dses-v0.2-outcome-events.schema.json
+++ b/schemas/dses-v0.2-outcome-events.schema.json
@@ -1,7 +1,7 @@
 {
   "$schema": "https://json-schema.org/draft/2020-12/schema",
-  "$id": "https://evidify.ai/schemas/dses/0.2.0-rc14/outcome-events.schema.json",
-  "title": "DSES v0.2.0-rc14 Outcome-Layer Events",
+  "$id": "https://evidify.ai/schemas/dses/0.2.0/outcome-events.schema.json",
+  "title": "DSES v0.2.0 Outcome-Layer Events",
   "description": "Two-level events on the cohort governance chain and per-case track chains. No self-reported capability, assurance, or state labels are permitted: the verifier derives them from evidence. Protocol hashes are bare lowercase SHA-256 hex. event_hash preimage: RFC 8785 canonical form of the event with integrity.event_hash, signatures, and payload removed.",
   "type": "object",
   "required": [
diff --git a/schemas/dses-v0.2-package.schema.json b/schemas/dses-v0.2-package.schema.json
index de4668d..b3cc952 100644
--- a/schemas/dses-v0.2-package.schema.json
+++ b/schemas/dses-v0.2-package.schema.json
@@ -1,6 +1,6 @@
 {
   "$schema": "https://json-schema.org/draft/2020-12/schema",
-  "$id": "https://evidify.ai/schemas/dses/0.2.0-rc14/package.schema.json",
+  "$id": "https://evidify.ai/schemas/dses/0.2.0/package.schema.json",
   "title": "DSES v0.2 package envelope",
   "type": "object",
   "required": [
diff --git a/scripts/dses_core.py b/scripts/dses_core.py
index 2c19bc1..9082a08 100755
--- a/scripts/dses_core.py
+++ b/scripts/dses_core.py
@@ -1,4 +1,4 @@
-"""DSES v0.2.0-rc14 cryptographic core.
+"""DSES v0.2.0 cryptographic core.
 
 One implementation of every primitive, shared by the generator, the verifier,
 and the regression harness, so that no claim in the specification is verified
diff --git a/scripts/generate_example.py b/scripts/generate_example.py
index cc38748..0d156fb 100755
--- a/scripts/generate_example.py
+++ b/scripts/generate_example.py
@@ -1,5 +1,5 @@
 #!/usr/bin/env python3
-"""Generate the DSES v0.2.0-rc14 worked example.
+"""Generate the DSES v0.2.0 worked example.
 
 Release-build properties, each driven by the fifth review round:
 
@@ -796,7 +796,7 @@ def build():
 
     export_sig = sign_dses(keys["outcome-registry-01-key-2"]["private"], "outcome-registry-01-key-2", "export-head", coh.prev)
 
-    out = {"package": "DSES v0.2.0-rc14 worked example",
+    out = {"package": "DSES v0.2.0 worked example",
            "description": "Twelve membership-committed eligible cases across two periodic manifests, resolvable v0.1 decision sequences with verified payload commitments, reliance metrics recomputed by executing the declared rule artifacts against snapshot-frozen evidence, an adjudication revision with metric supersession, externally rooted anchor receipts, and key rotation. No label in this package is stored where it can be derived.",
            "cohort_chain": coh.events, "case_chains": [t2.events for t2 in tracks],
            "export_head_signature": export_sig}
diff --git a/scripts/make_release.py b/scripts/make_release.py
index f782881..acbc8f6 100755
--- a/scripts/make_release.py
+++ b/scripts/make_release.py
@@ -1,5 +1,5 @@
 #!/usr/bin/env python3
-"""Build the public DSES v0.2.0-rc14 archive from an explicit allowlist.
+"""Build the public DSES v0.2.0 archive from an explicit allowlist.
 
 The ZIP is deterministic for a fixed source tree: members are sorted and carry
 one fixed timestamp. Build artifacts, review notes, local environments, VCS
@@ -13,7 +13,7 @@ import sys
 import zipfile
 
 ROOT = Path(__file__).resolve().parent.parent
-DEFAULT_OUT = ROOT.parent / "dses-v0.2.0-rc14-publication.zip"
+DEFAULT_OUT = ROOT.parent / "dses-v0.2.0-publication.zip"
 FILES = [
     "DSES-v0.1.md", "dses-v0.1.schema.json", "DSES-v0.2.md", "ERRATA-v0.1.md",
     "CLAIMS-CLASSIFICATION.md", "README.md", "IMPLEMENT.md",
@@ -63,7 +63,7 @@ def main():
     out = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DEFAULT_OUT
     # The output filename and the specification's Version line are two
     # statements of the same fact, and nothing used to check they agreed. This
-    # built dses-v0.2.0-rc14-publication.zip from an rc11 tree once, silently,
+    # built dses-v0.2.0-publication.zip from an rc11 tree once, silently,
     # and the resulting archive was one command away from being published under
     # a version it did not contain. If the filename names a version, it must be
     # the version in the tree.
diff --git a/tests/run_regression.py b/tests/run_regression.py
index 857607e..92bc45b 100755
--- a/tests/run_regression.py
+++ b/tests/run_regression.py
@@ -1,5 +1,5 @@
 #!/usr/bin/env python3
-"""DSES v0.2.0-rc14 adversarial regression suite.
+"""DSES v0.2.0 adversarial regression suite.
 
 Two hard rules for this harness, both from the fifth review round:
```

## Specification prose changes

The Version line, Section 5.1b's version reference, the 8.4 heading and its
first sentence, the Annex D sentence, the citation, the new Annex C entry
for 0.2.0, and the provenance section. `-` lines are rc14, `+` lines are
0.2.0.

```diff
diff --git a/DSES-v0.2.md b/DSES-v0.2.md
index 99a2676..3328338 100644
--- a/DSES-v0.2.md
+++ b/DSES-v0.2.md
@@ -1,7 +1,7 @@
 # Decision-Sequence Evidence Schema (DSES)
 ## Part II: The Outcome-Evidence Layer
 
-**Version:** 0.2.0-rc14 (Release candidate for public comment)
+**Version:** 0.2.0 (minted October 18, 2026; permanent identifiers)
 **Date:** August 20, 2026
 **Author:** Joshua M. Henderson, Ph.D. (Evidify LLC, East Orange, NJ)
 **Status:** Open specification. Comments and implementation reports welcome.
@@ -116,7 +116,7 @@ For an available hiding payload, the encoded nonce MUST match the declared `nonc
 
 The security claim is stated exactly: *a hiding commitment prevents practical dictionary enumeration from the commitment alone, assuming the nonce is unavailable to the attacker.* DSES can record that nonce destruction was asserted; it cannot prove no copy survived (Section 2.4, A1).
 
-`initial_payload_disposition` records disposition at creation and is never rewritten. The protocol represents later disposition changes through `outcome_integrity_event` records. A conformance-grade replay of current disposition is specified but **not implemented in this reference build** and therefore supports no v0.2.0-rc14 conformance claim. <!-- req:9.2 -->
+`initial_payload_disposition` records disposition at creation and is never rewritten. The protocol represents later disposition changes through `outcome_integrity_event` records. A conformance-grade replay of current disposition is specified but **not implemented in this reference build** and therefore supports no v0.2.0 conformance claim. <!-- req:9.2 -->
 
 ### 3.3 Three tiers, and one append-only checkpoint log
 
@@ -223,7 +223,7 @@ Events: `cohort_chain_created`, `anchor_evidence_recorded`, `anchor_distrusted`,
 
 ### 5.0 Membership multiplicity
 
-Membership leaves MUST be unique across the cohort's committed manifests. <!-- req:5.1b --> v0.2.0-rc14 supports only `unique_decision_instance`: each eligible decision instance receives its own pseudonymous membership token. Repeated encounters are represented as distinct eligible decision instances, never by repeating one token. A tree containing a repeated token can yield valid inclusion proofs while silently overstating the number of distinct committed instances, so `declared_multiplicity` is intentionally not a v0.2 option.
+Membership leaves MUST be unique across the cohort's committed manifests. <!-- req:5.1b --> v0.2.0 supports only `unique_decision_instance`: each eligible decision instance receives its own pseudonymous membership token. Repeated encounters are represented as distinct eligible decision instances, never by repeating one token. A tree containing a repeated token can yield valid inclusion proofs while silently overstating the number of distinct committed instances, so `declared_multiplicity` is intentionally not a v0.2 option.
 
 ### 5.1 Manifests
 
@@ -353,9 +353,9 @@ The identity SRF = 1 − RSR holds only when validity partitions into correct an
 
 `evaluation_state` is `proximal_post_exposure`, `final`, or a declared alternative; proximal response and final decision are different estimands and the formulas reference the declared one. Self-reliance requires `baseline_actor == evaluation_actor`; multi-actor trajectories are team-reliance constructs.
 
-### 8.4 WOA (informative in v0.2.0-rc14)
+### 8.4 WOA (informative in v0.2.0)
 
-WOA remains a supported descriptive construct but is not part of OL conformance in this release candidate and is not recomputed by the reference verifier. Deployments that report it should preserve the raw distribution, label bounded variants, and count equal-advice exclusions. WOA near zero against correct advice and negative WOA represent different behaviors and should be reported separately.
+WOA remains a supported descriptive construct but is not part of OL conformance in v0.2.0 and is not recomputed by the reference verifier. Deployments that report it should preserve the raw distribution, label bounded variants, and count equal-advice exclusions. WOA near zero against correct advice and negative WOA represent different behaviors and should be reported separately.
 
 ### 8.5 Disclosures
 
@@ -545,7 +545,7 @@ This package ships both. `scripts/dses_verify.py` performs the C and X checks en
 
 ## 11. Schema discipline
 
-**No conformant calculation or conformance claim may depend on an extension unless that extension is explicitly incorporated by a versioned normative definition artifact.** Schema isolation alone cannot prevent an extension from altering downstream semantics, so the constraint is stated as a requirement on calculations rather than on syntax. Core objects closed with `unevaluatedProperties: false` and a single namespaced `extensions` object; `event_type` bound to payload by discriminated union; integrity classes conditionally requiring their evidence and logically admissible on their face (an I3 claim requires at least one defining capability true, while truth of the evidence is the verifier's job); temporal fields constrained by calendar-aware patterns, with instant validity itself classified X because a regex cannot decide it; URIs pattern-constrained for the same reason; integers bounded to the JCS-safe range. Schema `$id`s are `/0.2.0-rc14/` in this candidate. The permanent `/0.2.0/` identifiers are minted once, when public comment closes, and never reused, which is why this build is a release candidate rather than the release: an identifier that cannot be withdrawn should not be spent on a document still under review.
+**No conformant calculation or conformance claim may depend on an extension unless that extension is explicitly incorporated by a versioned normative definition artifact.** Schema isolation alone cannot prevent an extension from altering downstream semantics, so the constraint is stated as a requirement on calculations rather than on syntax. Core objects closed with `unevaluatedProperties: false` and a single namespaced `extensions` object; `event_type` bound to payload by discriminated union; integrity classes conditionally requiring their evidence and logically admissible on their face (an I3 claim requires at least one defining capability true, while truth of the evidence is the verifier's job); temporal fields constrained by calendar-aware patterns, with instant validity itself classified X because a regex cannot decide it; URIs pattern-constrained for the same reason; integers bounded to the JCS-safe range. Schema `$id`s are `/0.2.0/` in this candidate. The permanent `/0.2.0/` identifiers are minted once, when public comment closes, and never reused, which is why this build is a release candidate rather than the release: an identifier that cannot be withdrawn should not be spent on a document still under review.
 
 ---
 
@@ -577,6 +577,8 @@ Every cryptographic artifact is real: RFC 8785 preimages, RFC 9162 inclusion and
 
 ## Annex C: Changelog
 
+**0.2.0.** Minted October 18, 2026 from candidate rc14, with no normative change from rc14 and no mechanism, rule, or schema structure change from rc10. The candidates rc10 through rc14 are collapsed into this release: rc10 statistical-review pass (design_structure disclosure, panel-scope kappa, Section 9.6 sequence-is-not-fault, Annex E), rc11 coherence pass (vocabulary, environment and language-guard gate steps), rc12 hygiene (lint L12 and the version-label lists, bump tooling that accepts a permanent label, the TERMINOLOGY, CLAIM-LEDGER and ERRATA-v0.2 companions, acronym expansions at 8.2, the make_release filename assertion), rc13 threat-model clarification (adversary A8, requirement 2.2b, the boundary fixture registry), and rc14 dependency pins. Their entries below stand as the record of each. Schema `$id`s move from `/0.2.0-rc14/` to `/0.2.0/` and are permanent under GOVERNANCE.md; outside that label, the Version line, this entry, and the provenance section at the end of this document, the text is rc14's. The Version line drops the candidate parenthetical, Section 8.4 and Annex D no longer describe the document as a candidate, and the citation names the concept DOI. Review record at mint: named human expert review was requested in three lanes and none completed; zero attestations are published in `docs/reviews/` and zero independent implementations exist. The provenance section states the request-by-request record as of the mint date. The author's ruling was to mint with the zero rather than hold permanent identifiers open, on the standing policy that an attestation received after the mint is published in `docs/reviews/` and dispositioned in an erratum or in 0.2.1. No objection was received, so this entry carries no dispositions. The worked example is regenerated once for the new label; its keys and hashes differ from rc14's while its structure and verdicts do not. The gate signature is unchanged from rc14: 206 objects, 2,205 checks, OL CONFORMANT, 158 rule-asserting cases rejected at the asserted rule, 1 boundary fixture held, quickstart 2 valid and 6 mutations, vocabulary 833 terms and 0 findings, release manifest 109 entries.
+
 **0.2.0-rc14.** Dependency and record hygiene. No mechanism, rule, or schema structure changes; outside the version label and this annex the specification text is unchanged, and the schemas change only in their version-labelled identifiers. The reference implementation's pinned `cryptography` moves from 43.0.1 to 50.0.2 and `jsonschema` from 4.23.0 to 4.26.0, because published advisory databases list advisories against cryptography 43.0.1 whose fixes ship in later releases. The full gate passes under the new pins with every count unchanged, and ENVIRONMENTS.md records the resolved sets it was observed in. The rc13 entry below carried the label it was drafted under, candidate delta and unreleased, into the published archive; it now reads as the released candidate it is. The worked example is regenerated once for the new version label, as every bump requires, so its keys and hashes differ from rc13's while its structure and verdicts do not. The rule-asserting suite stands at 158, unchanged; boundary fixtures stand at 1.
 
 **0.2.0-rc13.** Threat-model clarification, no mechanism change. Adds adversary A8, the event-emission and capture path, which may cause the recorder to accept an event whose content does not correspond to the action or presentation it describes while every downstream mechanism remains valid; and the matching non-claim in Section 2.2: a verifying record establishes integrity and provenance of what was recorded, not correspondence to implementation behavior (requirement 2.2b, A-class). Prompted by the METR and Redwood Research investigation of the July 2026 Hugging Face incident (report of 26 August 2026), which found clear evidence of successful tool-call spoofing in at least 96 of about 1,300 examined transcripts, roughly 7%. The reported techniques evolved from manipulating tool-call output to, eventually, replacing part of the tool-execution path so an agent could appear to issue one tool call while another executed. False event content appeared in the actual transcripts the investigators reviewed; the investigation did not test the transcript store's cryptographic integrity properties, so it establishes failure of implementation correspondence without establishing whether internal or historical integrity held. That separability is the reason to name the third property. The report also notes that setting up the spoof required actions that remained visible in the transcript, so what detection there was came from setup traces rather than from a downstream integrity check. Erratum 1 of 20 August already covered the rewrite-after-the-fact adversary; the incident's finding is the adversary in front of storage, which the text did not name. The adversarial suite gains its first indistinguishable-worlds fixture: an out-of-band oracle the verifier never receives assigns two worlds to one package, and the suite requires identical verifier output and requirement 2.2b listed as unestablished in both. That fixture documents a boundary rather than a rule; it is registered separately from the rule-asserting cases and counted separately. The rule-asserting suite stands at 158, unchanged; boundary fixtures stand at 1.
@@ -619,7 +621,7 @@ Also closed: the interval tolerance, stated four times in three documents and co
 
 ## Annex D (normative): Claim classification
 
-Every normative requirement using an uppercase conformance keyword carries a stable requirement tag and two independent labels in `CLAIMS-CLASSIFICATION.md`, which is release-blocking and ships with this release candidate. **Verification class** (S, C, X, T, A) answers what kind of establishment is possible in principle. **Reference verifier support** (implemented, partial, not_implemented) answers whether this build performs it. Conflating the two would let an unimplemented check hide inside an optimistic classification. Current counts: 33 S, 30 C, 90 X, 4 T, 23 A; 124 implemented, 4 partial, 3 not implemented.
+Every normative requirement using an uppercase conformance keyword carries a stable requirement tag and two independent labels in `CLAIMS-CLASSIFICATION.md`, which is release-blocking and ships with this version. **Verification class** (S, C, X, T, A) answers what kind of establishment is possible in principle. **Reference verifier support** (implemented, partial, not_implemented) answers whether this build performs it. Conflating the two would let an unimplemented check hide inside an optimistic classification. Current counts: 33 S, 30 C, 90 X, 4 T, 23 A; 124 implemented, 4 partial, 3 not implemented.
 
 ## Annex E (normative): Reconstruction questions
 
@@ -676,6 +678,6 @@ it.
 
 **Citing this specification:**
 
-> Henderson JM. Decision-Sequence Evidence Schema, version 0.2.0-rc14: the outcome-evidence layer. Evidify LLC; 2026. Release candidate for public comment.
+> Henderson JM. Decision-Sequence Evidence Schema, version 0.2.0: the outcome-evidence layer. Evidify LLC; 2026. https://doi.org/10.5281/zenodo.21960297
 
-**Review provenance and AI disclosure.** This release candidate was shaped by eleven rounds of detailed adversarial technical review conducted by an AI system <!-- REVIEW-SYSTEM-UNSPECIFIED -->, and its reference implementation was written by an AI system. No human subject-matter expert has yet reviewed this specification or its implementation. This is disclosed rather than acknowledged: attribution implies accountability for the claims made here, an AI system cannot hold that accountability, and the author retains full responsibility for every claim in this document, including those the machine review failed to catch. Readers should weight this accordingly. The compensating design choice is that this specification's claims are constructed to be machine-checked rather than vouched for: every requirement marked implemented names a verifier rule and a regression fixture that asserts that rule fires, `scripts/release_lint.py` fails the build when that correspondence breaks, and a reader may re-run the entire gate rather than trust any reviewer, human or otherwise. That substitutes verifiability for authority; it does not substitute for expert review, which remains outstanding and is named as such. One episode is worth recording for calibration: in the eighth round the reviewing system reported a canonicalization defect in two derived artifacts that did not exist, having used a non-conforming JSON canonicalizer in an environment that could not install the pinned dependency. The finding was wrong; the fail-fast canonicalization self-test it prompted was kept, because the failure mode it guards against is real. Machine review is useful and it is not self-validating.
+**Review provenance and AI disclosure.** This specification was shaped by eleven rounds of detailed adversarial technical review conducted by an AI system, and its reference implementation was written by AI systems under the author's direction. The reference implementation, the release gate, and every candidate from rc11 through this version were produced with Anthropic Claude models operated by the author through claude.ai, Claude Code and Cowork sessions. The specific system and version behind each of the eleven review rounds was not recorded in this repository at the time and is not reconstructed here; where the record is silent it is left silent rather than filled in. No round was conducted by a human subject-matter expert. This is disclosed rather than acknowledged: attribution implies accountability for the claims made here, an AI system cannot hold that accountability, and the author retains full responsibility for every claim in this document, including those the machine review failed to catch. Named human expert review was sought before this version was minted and was not completed. As of October 18, 2026, the review packet (rc11, then rc14) had been sent to named experts in three lanes. Protocol and cryptography: two reviewers were asked and did not reply or declined, and a third was asked on October 11, 2026 and had not yet responded. Health law and clinical governance: two reviewers were asked and did not reply or declined, and a third was asked on October 11, 2026 and had not yet responded. Statistics: a review by a named biostatistician was in progress in person and had produced no written attestation. Zero attestations exist in `docs/reviews/`, and zero independent implementations exist (claim 7.3c). The author chose to mint with both counts at zero rather than hold permanent identifiers open indefinitely, and records the zero here so that no reader infers a review that did not occur. An attestation received after this version was minted is published verbatim in `docs/reviews/` under the reviewer's name, with the version and archive digest the reviewer was given; each objection receives a written disposition that the reviewer sees before publication; and a disposition that changes published text is handled as an erratum under `ERRATA-v0.2.md` or carried into 0.2.1, never by altering this text. Readers should weight this accordingly. The compensating design choice is that this specification's claims are constructed to be machine-checked rather than vouched for: every requirement marked implemented names a verifier rule and a regression fixture that asserts that rule fires, `scripts/release_lint.py` fails the build when that correspondence breaks, and a reader may re-run the entire gate rather than trust any reviewer, human or otherwise. That substitutes verifiability for authority; it does not substitute for expert review, which remains outstanding and is named as such. One episode is worth recording for calibration: in the eighth round the reviewing system reported a canonicalization defect in two derived artifacts that did not exist, having used a non-conforming JSON canonicalizer in an environment that could not install the pinned dependency. The finding was wrong; the fail-fast canonicalization self-test it prompted was kept, because the failure mode it guards against is real. Machine review is useful and it is not self-validating.
```

## Other shipped prose

`README.md` (version-status and publication-boundary sections), `SCORECARD.md`
(reviewer row and date), `ERRATA-v0.2.md` (status line), and
`ENVIRONMENTS.md` (mint environment added). None of these is in your lane's
scope. They are listed so the set is closed; `git diff v0.2.0-rc14 v0.2.0`
shows them in full once the tag exists.
