"""DSES v0.2.0-rc3 reference metric derivation engine.

This module contains the orchestration that turns projected v0.1 trajectories
and snapshot-frozen adjudications into RAIR/RSR/EAR numerator-denominator
counts and disclosure exclusions. The generator and reference verifier both
call this exact function. Rule-specific semantics remain in separately hashed
modules under rules/.
"""


def recompute_metric(records, binary_mod, metric_mod, alignment_mod):
    """Return ``(numerator, denominator, used_hashes, exclusions)``.

    Each record supplies:
      - trajectory: projected baseline/AI/evaluation state and commensurability
      - conclusion_status / conclusion: snapshot-frozen adjudication result
      - adjudication_hash: the evidence event consumed when the case contributes

    The binary validity, alignment, and metric contribution semantics are all
    delegated to the executable rule modules declared by the package. This
    function owns only the deterministic orchestration and exclusion
    accounting. In particular the alignment relation EAR depends on is NOT
    computed here: it was an inline equality until rc3, which made the relation
    undeclared and undigested in violation of Section 4.
    """
    numerator = denominator = 0
    used_hashes = []
    exclusions = {
        "indeterminate": 0,
        "commensurability": 0,
        "partially_correct": 0,
        "not_classifiable": 0,
    }

    for record in records:
        trajectory = record["trajectory"]
        if record.get("conclusion_status") != "determinate":
            exclusions["indeterminate"] += 1
            continue
        if not trajectory.get("commensurable", False):
            exclusions["commensurability"] += 1
            continue

        conclusion = record.get("conclusion")
        vb = binary_mod.classify(trajectory["baseline"], conclusion)
        va = binary_mod.classify(trajectory["ai"], conclusion)
        ve = binary_mod.classify(trajectory["evaluation"], conclusion)
        projected = (binary_mod.binary(vb), binary_mod.binary(va), binary_mod.binary(ve))
        if any(v is None for v in projected):
            key = "partially_correct" if "partially_correct" in (vb, va, ve) else "not_classifiable"
            exclusions[key] += 1
            continue

        aligned = alignment_mod.aligns(trajectory["evaluation"], trajectory["ai"])
        dd, nn = metric_mod.contributes(vb, va, ve, aligned)
        denominator += dd
        numerator += nn
        if dd:
            used_hashes.append(record["adjudication_hash"])

    return numerator, denominator, sorted(used_hashes), exclusions
