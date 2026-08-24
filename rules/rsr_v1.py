"""RSR: P(E correct | baseline correct, AI incorrect). SRF = 1 - RSR."""
RULE_ID = "rsr-v1"


def contributes(vb, va, ve, aligned_same):
    if vb == "correct" and va == "incorrect":
        return 1, 1 if ve == "correct" else 0
    return 0, 0
