"""Eligibility rule pe-eligibility-v1: ED encounter with CTPA ordered or
considered (SNOMED 241541005), age 18 or older."""
RULE_ID = "pe-eligibility-v1"


def eligible(encounter):
    return "241541005" in encounter.get("codes", []) and encounter.get("age", 0) >= 18
