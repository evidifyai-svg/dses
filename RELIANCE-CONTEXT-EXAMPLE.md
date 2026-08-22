# What a per-clinician DSES metric looks like when it cannot be stripped

This is a real artifact from the DSES v0.2 worked example, not an illustration.
It is `examples/derived/derived-rair-subject-0417-v1.json`, and every number
below is recomputed by the reference verifier from snapshot-frozen evidence. The
artifact does not assert these figures; a verifier that disagreed with any of
them would reject the package.

It exists to answer one question: what happens when an administrator or a review
board asks a longitudinal DSES record about a single clinician.

---

## The rate, on its own

> **Reliance on AI Rescue (RAIR): 1 of 3, or 33%**

That is the number a committee would be handed. Read alone it invites a
conclusion: in two of three opportunities where the AI could have corrected this
reader, the reader did not take it.

## The same artifact, as DSES requires it to travel

**Subject:** clinician-0417
**Observation window:** 2026-03-01 to 2026-06-30, 121 days
**Governance:** departmental quality improvement, advisory consequence only
**95% interval (Wilson): 6% to 79%**

**Balanced reliance context, over all 10 of this reader's assigned decision
instances in the window (not merely the 8 metric-eligible ones):**

| | |
|---|---|
| Assigned decision instances | 10 |
| Linkage | 9 linked, 1 decision record missing |
| Maturation | 8 mature, 1 pending, 1 not applicable |
| Adjudication | 7 determinate, 1 indeterminate, 2 not adjudicated |
| Metric-eligible | 8 |

Two of this reader's instances never became metric-eligible, and the context
says so. A context computed only over eligible cases could not; a reader whose
sequences were disproportionately lost would look statistically pristine.

**Over the 8 metric-eligible cases:**

| | Correct | Incorrect | Excluded |
|---|---|---|---|
| This reader's independent baseline judgment | 2 | 5 | 1 |
| **The AI's output** | **6** | **1** | **1** |
| The reader's judgment after seeing the AI | 3 | 3 | 2 |

| | |
|---|---|
| Adjudication status | 7 determinate, 1 indeterminate |
| Commensurability | 7 commensurable, 1 noncommensurable |
| AI system | vendor-pe-cad-2.1 (all 8) |
| Exposure class | 7 categorical, 1 directive |

---

## What the context changes

**The interval swallows the estimate.** 1 of 3 is 33%, and the 95% interval runs
from 6% to 79%. Three opportunities cannot distinguish a reader who ignores
useful AI from one who does not. The minimum cell size in the governance artifact
exists to stop numbers this thin from being reported at all, and the interval is
mandatory precisely so a point estimate cannot travel alone.

**The denominator is not "cases where AI advice was available."** It is the three
cases where this reader was wrong and the AI was right. Twenty-five of the
reader's other decision-opportunities are not in it. A rate conditioned this
narrowly cannot be read as a general disposition toward AI.

**The AI was wrong in one of eight cases here.** Any statement about this reader's
reliance has to sit beside the reader's own error rate, the AI's error rate, and
the fact that one case was not commensurable and one was never adjudicated. The
context is recomputed over the reader's whole bounded window, not over the
denominator of whichever rate is being displayed, which is what stops the
flattering or damning slice from being shown by itself.

**The window is bounded and was declared in advance.** 121 days, inside the 180
authorised by governance. A career-scale accumulation is not implicit permission
to use an entire career.

## What DSES refuses to say

The artifact carries no determination of competence, standard of care, reasonable
AI use, or negligence, and the schema forbids such a field. This one is advisory,
for quality improvement, and its governance artifact would have to say otherwise
before the analysis ran. Where the declared consequence is credentialing,
employment, litigation support, or regulatory oversight, governance must state
that an aggregate metric is not a sufficient sole basis for adverse action, that
case-level review is required, that the subject is notified and can see the
evidence, and that an appeal exists.

DSES can establish that those safeguards were declared before the analysis. It
cannot establish that anyone honoured them. That remains an attested requirement,
not a verified one, and the specification says so.

---

*Reproduce: `bash run_all.sh` in the DSES v0.2 package. The verifier recomputes
every figure above and rejects the package if any one of them is wrong.*
