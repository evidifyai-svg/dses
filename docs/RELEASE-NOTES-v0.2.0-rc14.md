# DSES v0.2.0-rc14 release notes (working record, docs/, not in the archive)

Prepared 2026-10-11. Dependency and record hygiene. No mechanism change, no
schema structure change, no new rule.

## What rc14 changes

- `requirements.txt` moves `cryptography` from 43.0.1 to 50.0.2 and
  `jsonschema` from 4.23.0 to 4.26.0. Against the rc13 pins, pip-audit lists
  ten advisories for cryptography 43.0.1, with fixes released from 44.0.1
  through 49.0.0. Against the rc14 pins it lists none. `jcs` stays at 0.2.1,
  its current release.
- Annex C: the rc13 entry's heading drops "candidate delta, unreleased", a
  label written before that version was cut and carried into its archive.
  The rc13 review packet disclosed it; this candidate corrects it.
- `ENVIRONMENTS.md`: Environment A's direct pins are updated, and a new
  Environment C records the resolved set this candidate was built and gated
  in. Environment B (macOS) still names rc11 and stays a stated gap until the
  gate is observed there on the new pins.
- The worked example is regenerated once for the new version label. Its keys
  and hashes differ from rc13's; its structure and verdicts do not.

## Why now

The review packet asks every reviewer, the protocol and cryptography lane
included, to install the pinned requirements and run the gate. Pins with
published advisories are the wrong thing to hand a cryptographer. Whether any
of those advisories reaches a DSES code path was not assessed. The pins move
because they are what every reader installs.

## Counts

Unchanged from rc13: 206 objects, 2205 checks, OL CONFORMANT, 158
rule-asserting cases rejected at the asserted rule, 1 boundary fixture held,
quickstart 2 valid examples and 6 targeted mutations, vocabulary 833 terms and
0 findings, release manifest 109 entries, archive 110 members.

## Gate

ALL GREEN in Environment C on this tree, under the new pins. The archive built
from this tree has sha256
`ac0cd7998249ede899cd4a735cf68e03ec86026b1411950098ae46e83f970133`. Rebuilding
from the merged tree must reproduce it exactly; if it does not, stop before
tagging.

## Not in rc14

No normative change. Outside the version label and Annex C, the specification
text is unchanged.
