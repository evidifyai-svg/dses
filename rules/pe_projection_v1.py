"""Executable projection rule pe-projection-v1.

Baseline: last preliminary_read_committed before the first ai_output_released.
Target exposure: first ai_output_released.
Evaluation state: proximal_post_exposure (first post_exposure_read_committed
after the target exposure).
Coexposure: any second ai_output_released excludes the projection.
Actor identity: baseline actor must equal evaluation actor.
"""
RULE_ID = "pe-projection-v1"
ELIGIBLE_EXPOSURE_CLASSES = ["PRESENCE", "CATEGORICAL", "LOCALIZATION", "QUANTITATIVE"]


def project(events):
    expos = [e for e in events if e["event_type"] == "ai_output_released"]
    if not expos:
        return None
    if len(expos) > 1:
        return {"excluded": "coexposure"}
    target = expos[0]
    pres = [e for e in events if e["event_type"] == "preliminary_read_committed" and e["sequence"] < target["sequence"]]
    posts = [e for e in events if e["event_type"] == "post_exposure_read_committed" and e["sequence"] > target["sequence"]]
    if not pres or not posts:
        return None
    baseline, evaluation = pres[-1], posts[0]
    return {
        "baseline": baseline["payload"]["judgment"],
        "ai": target["payload"]["output"],
        "evaluation": evaluation["payload"]["judgment"],
        "exposure_class": target["payload"]["exposure_class"],
        "ai_system_ref": target["payload"].get("ai_system_ref", "UNKNOWN"),
        "baseline_actor": baseline["payload"]["actor_ref"],
        "evaluation_actor": evaluation["payload"]["actor_ref"],
        "commensurable": target["payload"]["exposure_class"] in ELIGIBLE_EXPOSURE_CLASSES,
        "baseline_sequence": baseline["sequence"],
        "exposure_sequence": target["sequence"],
        "evaluation_sequence": evaluation["sequence"],
    }
