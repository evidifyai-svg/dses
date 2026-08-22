"""EAR: P(E incorrect AND E aligns same as AI | baseline correct, AI incorrect).

The incorrectness conjunction bounds EAR by SRF by construction.
"""
RULE_ID = "ear-v1"


def contributes(vb, va, ve, aligned_same):
    if vb == "correct" and va == "incorrect":
        return 1, 1 if (ve == "incorrect" and aligned_same) else 0
    return 0, 0
