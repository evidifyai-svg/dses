# ERRATA: DSES v0.1.0

**Date:** August 20, 2026
**Applies to:** DSES v0.1.0 (August 15, 2026)
**Status:** Normative correction. v0.1.0 text remains published unaltered; this erratum travels with it.

## Erratum 1: The I2 detection claim (Section 7, integrity class table)

**Original text:** I2: "... Any post-hoc insertion, deletion, or modification within the chain is detectable by any third party holding the export."

**Problem.** The claim is too strong. An operator who controls the complete history can alter an event and recompute every downstream hash, producing a second, internally consistent chain. A third party holding only the rewritten export verifies it successfully. Hash chaining establishes internal consistency; detection of rewriting requires a trust anchor outside the operator: a previously witnessed export, a published checkpoint, or external anchoring (I3(b)). Certificate Transparency's consistency proofs are proofs between a current tree and a previously known tree head for exactly this reason.

**Corrected text.** I2 provides: "Demonstrable internal consistency, and detection of any insertion, deletion, or modification relative to a previously witnessed export or checkpoint. Any third party holding both a previously obtained export (or its chain head) and a later export can mechanically detect rewriting between them. A single export establishes internal consistency only. Historical immutability against the operator requires a trust anchor outside the operator: witnessed checkpoints or external anchoring (I3(b))."

**Consequential edits.** Section 7.1 (honest labeling) gains: "An I2 record MUST NOT be described as proving historical immutability absent a named checkpoint or anchor; tamper-evidence claims MUST name the trust anchor they are relative to." Section 12's example conformance language becomes: "... hash-chained event log with offline third-party verification of internal consistency and checkpoint-relative tamper evidence."

**Why an erratum rather than a silent v0.2 fix.** v0.1 Section 7.1 requires that lower-class records not be presented with higher-class language. That obligation applies to the specification itself. The correction is published as an erratum against v0.1, five days after v0.1, prompted by public technical review, because the honest-labeling rule is only credible if the specification submits to it first.

Henderson JM, Evidify LLC.
