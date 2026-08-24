"""RAIR: P(E correct | baseline incorrect, AI correct)."""
RULE_ID = "rair-v1"


def contributes(vb, va, ve, aligned_same):
    if vb == "incorrect" and va == "correct":
        return 1, 1 if ve == "correct" else 0
    return 0, 0
