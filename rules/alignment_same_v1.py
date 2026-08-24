"""Alignment relation alignment-same-v1.

EAR's conjunction asks whether the evaluation state aligns with the AI output.
This module is the declared, content-addressed answer to that question, because
Section 4 requires alignment relations to carry an executable identifier and
fixtures exactly as projection rules and estimators do. Before rc3 the relation
existed only as an inline equality inside the reference verifier, which is the
condition Section 4 prohibits.

Scope. For this relation, alignment means exact agreement with the AI output.
It is declared valid only for answer spaces whose semantics are `nominal`, and
the verifier enforces that against the criterion's declared
`answer_space_semantics` rather than leaving it as prose. Ordered, interval, or
continuous answer spaces require a different alignment relation, declared and
digested separately, because "toward" presupposes an order that a nominal space
does not carry.
"""
RULE_ID = "alignment-same-v1"
ANSWER_SPACE_REQUIREMENT = "nominal"


def aligns(evaluation, ai_output):
    """True when the evaluation state adopted the AI's answer."""
    if evaluation is None or ai_output is None:
        return False
    return evaluation == ai_output
