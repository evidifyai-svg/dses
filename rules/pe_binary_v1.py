"""Executable binary validity projection pe-binary-v1.

Validity of a judgment against an adjudicated conclusion over the answer space
{positive, negative, equivocal}. Equivocal judgments are partially_correct and
excluded by the binary projection; missing inputs are not_classifiable.
"""
RULE_ID = "pe-binary-v1"
EXCLUDED = ("partially_correct", "not_classifiable")


def classify(judgment, conclusion):
    if judgment is None or conclusion is None:
        return "not_classifiable"
    if judgment == "equivocal":
        return "partially_correct"
    return "correct" if judgment == conclusion else "incorrect"


def binary(validity):
    return None if validity in EXCLUDED else validity
