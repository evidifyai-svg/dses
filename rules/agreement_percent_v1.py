"""Inter-adjudicator agreement agreement-percent-v1.

Percent agreement over pre-consensus assessments only.

The rule that was ambiguous in prose and is now decided here: an assessment
recorded as NOT assessable is a category that agrees with itself. Two
adjudicators who independently conclude the evidence does not support a
determination have agreed, and scoring that as disagreement would penalise a
panel for consistent honesty about missing evidence. The alternative reading
(non-assessable agrees with nothing) is defensible and produces a different
number, which is precisely why the choice must be executable rather than
implied.
"""
RULE_ID = "agreement-percent-v1"
NOT_ASSESSABLE = "__not_assessable__"


def category(assessment):
    """Collapse one assessment to its comparison category."""
    if not assessment.get("assessable", False):
        return NOT_ASSESSABLE
    return assessment.get("conclusion")


def agreement(assessments):
    """Percent agreement: the share of assessments matching the modal category.

    Two assessments, both non-assessable, agree: value 1.
    """
    cats = [category(a) for a in assessments]
    if not cats:
        return None
    top = max(set(cats), key=cats.count)
    return cats.count(top) / len(cats)
