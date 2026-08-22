"""Decision rule pe-decision-v1: map adequate evidence to a conclusion;
inadequate evidence is indeterminate (treated course without confirmation)."""
RULE_ID = "pe-decision-v1"


def decide(imaging, course, treated_without_confirmation):
    if treated_without_confirmation:
        return ("indeterminate", None)
    from pe_composite_v1 import compose
    c = compose(imaging, course)
    return ("determinate", c) if c is not None else ("not_assessable", None)
