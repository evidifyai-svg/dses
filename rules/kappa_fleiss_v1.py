"""Panel-scope chance-corrected agreement kappa-fleiss-v1.

Fleiss' kappa over the pre-consensus assessments of a set of adjudicated
items. This rule is PANEL-SCOPE and is not interchangeable with
agreement-percent-v1, which is item-scope.

Why the scope is part of the rule and not an afterthought. Percent agreement is
defined for a single item: it is the share of that item's assessments falling in
its modal category, and it needs nothing outside the item. Chance correction is
not, because the chance term is estimated from the marginal category
distribution across items. Computed over one item the marginal distribution IS
the observed distribution, so expected agreement equals observed agreement and
kappa is 0/0. For the two-assessor unanimous item that dominates real
adjudication panels this is not an edge case, it is the common case. A charter
that named a chance-corrected statistic in the item-scope slot would therefore
be declaring a statistic that is undefined on most of its own record, which is
the failure mode Section 3.8 exists to prevent. The two statistics occupy
separate charter fields for that reason.

Balanced panels only. Every item must carry the same number of assessments.
Unbalanced panels admit at least two defensible generalizations (weighting each
item equally, or weighting by that item's assessment pairs), which produce
different numbers from the same evidence. This rule declines rather than
choosing silently: a charter needing an unbalanced panel must declare a
different rule that states its convention executably.

Categories are the same collapse agreement-percent-v1 uses, so the two
statistics describe the same assessments: a non-assessable assessment is a
category that agrees with itself.
"""
RULE_ID = "kappa-fleiss-v1"
NOT_ASSESSABLE = "__not_assessable__"
SCOPE = "panel"


def category(assessment):
    """Collapse one assessment to its comparison category."""
    if not assessment.get("assessable", False):
        return NOT_ASSESSABLE
    return assessment.get("conclusion")


def panel_agreement(items):
    """Fleiss' kappa over ``items``, a list of per-item assessment lists.

    Returns None where kappa is not defined: fewer than two items, fewer than
    two assessments on an item, an unbalanced panel, or expected agreement of
    exactly 1 (a single observed category, where no chance-corrected statistic
    carries information).
    """
    rows = [[category(a) for a in item] for item in items]
    if len(rows) < 2:
        return None
    n = len(rows[0])
    if n < 2 or any(len(r) != n for r in rows):
        return None

    cats = sorted({c for r in rows for c in r}, key=lambda c: (c is None, str(c)))
    total = len(rows) * n

    p_bar = sum((sum(r.count(c) ** 2 for c in cats) - n) / (n * (n - 1)) for r in rows) / len(rows)
    p_e = sum((sum(r.count(c) for r in rows) / total) ** 2 for c in cats)
    if p_e == 1:
        return None
    return (p_bar - p_e) / (1 - p_e)
