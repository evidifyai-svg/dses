"""Composite rule pe-composite-v1: PE positive if confirmatory imaging is
positive, else positive if the 90-day clinical course meets the embolic
composite, else negative when both sources are adequate and negative."""
RULE_ID = "pe-composite-v1"


def compose(imaging, course):
    if imaging == "positive" or course == "positive":
        return "positive"
    if imaging == "negative" and course == "negative":
        return "negative"
    return None
