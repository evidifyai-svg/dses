#!/usr/bin/env python3
"""Generate the DSES v0.2.0-rc3 worked example.

Release-build properties, each driven by the fifth review round:

  * The anchor trust root lives OUTSIDE the package: the generator writes
    examples/anchor-trust-store.json, which represents out-of-band key
    distribution. The genesis key directory does not contain the anchor key.
  * Every code_artifact_digest is the SHA-256 of the actual rule module bytes
    in rules/, and derivation_software_digest is the SHA-256 of the actual
    derivation orchestration engine (scripts/dses_derivation.py). Names are not code.
  * v0.1 decision events carry payload commitments like every other DSES event,
    and the verifier checks them.
  * Two eligibility manifests (March, April); each track binds to its manifest
    by event hash.
  * Snapshots ship their population tuples so the root is recomputable and
    metrics can be recomputed against the frozen state, not the live chains.
  * Metric artifacts carry Wilson intervals per their declared estimator, and
    no stored prespecification or assurance labels anywhere.

Run from the package root: python3 scripts/generate_example.py
"""
import json
from collections import Counter
import os
import secrets
import sys

from cryptography.hazmat.primitives.asymmetric import ed25519

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dses_core import (  # noqa: E402
    anchor_receipt_body, anchor_receipt_target, artifact_content_hash, canon,
    consistency_path, event_preimage_hash, file_digest, h, inclusion_path,
    mth, sign_dses, wilson_interval,
)
from dses_derivation import recompute_metric  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RULES = os.path.join(ROOT, "rules")
COHORT = "cohort-chain-pe-2026"

# case, baseline, ai, evaluation, conclusion, conclusion_status, exposure, linkage, manifest
CASES = [
    ("c00", "negative", "positive", "positive", "positive", "determinate", "CATEGORICAL", "linked", 0),
    ("c01", "negative", "positive", "negative", "positive", "determinate", "CATEGORICAL", "linked", 0),
    ("c02", "positive", "negative", "positive", "positive", "determinate", "CATEGORICAL", "linked", 0),
    ("c03", "positive", "negative", "negative", "positive", "determinate", "CATEGORICAL", "linked", 0),
    ("c04", "positive", "negative", "equivocal", "positive", "determinate", "CATEGORICAL", "linked", 0),
    ("c05", "positive", "positive", "positive", "positive", "determinate", "CATEGORICAL", "linked", 0),
    ("c06", "negative", "negative", "negative", "positive", "determinate", "CATEGORICAL", "linked", 0),
    ("c07", "negative", "positive", "positive", "positive", "determinate", "DIRECTIVE", "linked", 0),
    ("c08", "negative", "positive", "positive", None, "indeterminate", "CATEGORICAL", "linked", 1),
    ("c09", "negative", "positive", "equivocal", "positive", "determinate", "CATEGORICAL", "linked", 1),
    ("c10", None, None, None, None, None, None, "decision_record_missing", 1),
    ("c11", "positive", "negative", "positive", None, None, "CATEGORICAL", "immature", 1),
]


def digest_obj(x):
    return {"alg": "sha-256", "digest": x}


def rule_digest(rule_id):
    return digest_obj(file_digest(os.path.join(RULES, rule_id.replace("-", "_") + ".py")))


RULE_PARAMETERS = {
    "alignment-same-v1": {"answer_space_requirement": "nominal"},
    "binomial-point-v1": {"interval_method": "Wilson", "level": 0.95,
                          "tolerance": 1e-9, "tolerance_kind": "absolute",
                          "quantiles": {"0.95": 1.959963984540054, "0.99": 2.5758293035489004}},
}


def executable(rule_id):
    locator = f"rules/{rule_id.replace('-', '_')}.py"
    exe = {"rule_id": rule_id,
           "code_artifact": {"media_type": "text/x-python", "locator": locator,
                             "digest": rule_digest(rule_id)},
           "fixtures_ref": f"fixtures/{rule_id}.fixtures.json"}
    if rule_id in RULE_PARAMETERS:
        exe["parameters"] = RULE_PARAMETERS[rule_id]
    return exe


def aref(a):
    return {"artifact_id": a["artifact_id"], "version": a["version"], "content_hash": digest_obj(a["content_hash"])}


def integrity():
    return {"integrity_class": "I2", "canonicalization": "RFC8785"}


class Chain:
    def __init__(self, scope, ref):
        self.scope, self.ref, self.events, self.prev, self.seq = scope, ref, [], None, 0

    def add(self, etype, payload, when, *, hiding=False, actor=None, nonces=None):
        c = canon(payload)
        if hiding:
            nonce = secrets.token_bytes(16)
            pc = {"alg": "sha-256", "digest": h(nonce + c), "commitment_type": "hiding", "nonce_bits": 128}
        else:
            pc = {"alg": "sha-256", "digest": h(c), "commitment_type": "content_digest"}
        ev = {"event_id": f"{self.ref}-{self.seq:04d}", "event_type": etype, "chain_scope": self.scope,
              "chain_ref": self.ref, "sequence": self.seq, "occurred_at": when, "recorded_at": when,
              "payload_commitment": pc, "initial_payload_disposition": "available",
              "integrity": integrity(), "source_system": "outcome-registry-01", "payload": payload}
        if actor:
            ev["actor"] = actor
        if self.prev:
            ev["integrity"]["prev_event_hash"] = self.prev
        ev["integrity"]["event_hash"] = event_preimage_hash(ev)
        if hiding:
            nonces[ev["integrity"]["event_hash"]] = nonce.hex()
        self.prev, self.seq = ev["integrity"]["event_hash"], self.seq + 1
        self.events.append(ev)
        return ev

    def head_obs(self, epoch):
        return {"chain_ref": self.ref, "head_sequence": self.seq - 1, "head_hash": self.prev, "checkpoint_epoch": epoch}


SUBJECT = "clinician-0417"
SUBJECT_CASES = {"c00", "c01", "c02", "c03", "c05", "c07", "c08", "c09", "c10", "c11"}


def actor_for(case):
    """Most reader studies are not one case per clinician. One reader owning a
    slice of the cohort is what makes an individual-level derivation meaningful,
    and what makes its balanced context worth reading."""
    return SUBJECT if case in SUBJECT_CASES else f"clinician-{case}"


def build_decision_sequence(case, baseline, ai, evaluation, exposure_class):
    ch = Chain("decision", f"decision-chain-{case}")
    ch.add("case_opened", {"workflow_ref": "ed-cta-workflow-v3", "actor_ref": actor_for(case)}, "2026-03-10T02:00:00Z")
    ch.add("preliminary_read_committed", {"actor_ref": actor_for(case), "judgment": baseline,
                                          "answer_space": ["positive", "negative", "equivocal"],
                                          "independence_class": "UNEXPOSED"}, "2026-03-10T02:10:00Z")
    ch.add("ai_output_released", {"ai_system_ref": "vendor-pe-cad-2.1", "exposure_class": exposure_class,
                                  "output": ai, "answer_space": ["positive", "negative", "equivocal"]}, "2026-03-10T02:11:00Z")
    ch.add("post_exposure_read_committed", {"actor_ref": actor_for(case), "judgment": evaluation,
                                            "independence_class": "DIRECTLY_EXPOSED"}, "2026-03-10T02:20:00Z")
    fin = ch.add("final_decision_committed", {"actor_ref": actor_for(case), "decision": evaluation, "terminal": True},
                 "2026-03-10T02:25:00Z")
    return ch, fin


def build():
    nonces, keys = {}, {}

    def newkey(ref):
        sk = ed25519.Ed25519PrivateKey.generate()
        keys[ref] = {"private": sk, "public": sk.public_key().public_bytes_raw().hex()}
        return sk

    newkey("outcome-registry-01-key-1")
    newkey("outcome-registry-01-key-2")
    ed_key = newkey("ed-information-system-key-1")
    anchor_key = newkey("anchor-authority-01-key-1")

    # The anchor authority's key is distributed OUT OF BAND. It is written to the
    # external trust store and deliberately excluded from the genesis directory.
    json.dump({"note": "External anchor trust store. Represents out-of-band key distribution; "
                       "the verifier trusts receipts ONLY against keys bound here, never against "
                       "keys carried inside the (operator-rewritable) package.",
               "authorities": {"anchor-authority-01": {"alg": "ed25519",
                                                       "public_key": keys["anchor-authority-01-key-1"]["public"],
                                                       "key_ref": "anchor-authority-01-key-1"}}},
              open(os.path.join(ROOT, "examples", "anchor-trust-store.json"), "w"), indent=2)

    key_directory = [
        {"key_ref": "outcome-registry-01-key-1", "alg": "ed25519", "public_key": keys["outcome-registry-01-key-1"]["public"],
         "valid_from": "2026-02-01T00:00:00Z", "valid_to": "2026-07-01T00:00:00Z"},
        {"key_ref": "outcome-registry-01-key-2", "alg": "ed25519", "public_key": keys["outcome-registry-01-key-2"]["public"],
         "valid_from": "2026-06-01T00:00:00Z"},
        {"key_ref": "ed-information-system-key-1", "alg": "ed25519", "public_key": keys["ed-information-system-key-1"]["public"],
         "valid_from": "2026-02-01T00:00:00Z"},
    ]

    def mk(b):
        b["content_hash"] = artifact_content_hash(b)
        return b

    charter = mk({
        "artifact_kind": "adjudication_charter", "artifact_id": "https://example.org/dses/charters/pe-panel-2026",
        "version": "1.0.0", "created_at": "2026-02-15T00:00:00Z", "author_ref": "study-methods-group",
        "prespecification_cutoff": {"cutoff_type": "before_first_enrollment", "cutoff_time": "2026-03-01T00:00:00Z"},
        "roster": [{"adjudicator_ref": "adj-A", "role": "member", "qualification_ref": "cv-adj-A"},
                   {"adjudicator_ref": "adj-B", "role": "member", "qualification_ref": "cv-adj-B"},
                   {"adjudicator_ref": "adj-C", "role": "chair", "qualification_ref": "cv-adj-C"}],
        "independence_attestations": ["No adjudicator participated in index care.",
                                      "No adjudicator has a financial interest in the AI system."],
        "blinding_plan": {"included_evidence_categories": ["index_imaging_deidentified", "clinical_course_abstract"],
                          "excluded_evidence_categories": ["ai_output", "post_ai_documentation", "co_adjudicator_conclusions"]},
        "assessment_protocol": {"committed_before_consensus": True, "min_independent_assessments": 2},
        "agreement_statistic": executable("agreement-percent-v1"),
        "disagreement_pathway": {"method": "third_reader", "procedure": "Chair adjudicates after independent commitment."},
        "revision_protocol": {"authorized_methods": ["consensus", "third_reader", "chair_ruling"],
                              "assessment_free_methods": ["chair_ruling"],
                              "deciding_role": "chair"},
        "minimum_data_rule": "Index imaging plus 90-day course required.",
        "status_tracking_cadence": "P30D", "deviation_handling": "Deviations recorded as process_flags.",
    })
    criterion = mk({
        "artifact_kind": "evaluation_criterion", "criterion_type": "clinical_reference_standard",
        "artifact_id": "https://example.org/dses/criteria/pe-90day-composite", "version": "1.0.0",
        "created_at": "2026-02-15T00:00:00Z", "author_ref": "study-methods-group",
        "prespecification_cutoff": {"cutoff_type": "before_first_enrollment", "cutoff_time": "2026-03-01T00:00:00Z"},
        "target_construct": {"description": "Pulmonary embolism present at index encounter",
                             "code_sets": [{"system": "SNOMED CT", "system_version": "2026-03-01", "codes": ["59282003"]}]},
        "target_timepoint": "index encounter",
        "answer_space": ["positive", "negative", "equivocal"],
        "answer_space_semantics": "nominal",
        "clinical_reference_standard": {
            "evidence_sources": ["imaging_followup", "clinical_course", "panel_opinion"],
            "timing": {"mode": "delayed", "window": "P90D"},
            "composition": {"mode": "composite", "composite_rule": executable("pe-composite-v1")},
            "determination_mechanism": {"mode": "human_adjudication", "adjudication_charter_ref": aref(charter)},
            "outcome_window": "P90D",
            "missing_data_handling": "No imaging and no 90-day course: not_assessable.",
            "indeterminate_case_handling": "Treated course without confirmatory imaging: indeterminate, excluded from binary metrics.",
            "intercurrent_event_policy": [{"event_class": "anticoagulation_initiated", "strategy": "hypothetical"}],
        },
        "binary_validity_projection": {"correct_states": ["correct"], "incorrect_states": ["incorrect"],
                                       "excluded_states": ["partially_correct", "not_classifiable"],
                                       "executable": executable("pe-binary-v1")},
        "decision_rule": executable("pe-decision-v1"),
    })
    projection = mk({
        "artifact_kind": "projection_rule", "artifact_id": "https://example.org/dses/projections/pe-primary",
        "version": "1.0.0", "created_at": "2026-02-15T00:00:00Z", "author_ref": "study-methods-group",
        "prespecification_cutoff": {"cutoff_type": "before_first_ai_exposure", "cutoff_time": "2026-03-01T00:00:00Z"},
        "baseline_selection": "Last preliminary_read_committed before the first ai_output_released.",
        "target_exposure_selection": "First ai_output_released for the index study.",
        "evaluation_state": "proximal_post_exposure",
        "eligible_exposure_classes": ["PRESENCE", "CATEGORICAL", "LOCALIZATION", "QUANTITATIVE"],
        "coexposure_handling": "exclude_projection",
        "actor_identity_requirement": "baseline_equals_evaluation_actor",
        "executable": executable("pe-projection-v1"),
    })

    def metric_artifact(name, rid):
        return mk({
            "artifact_kind": "metric_definition",
            "artifact_id": f"https://example.org/dses/metrics/{name.lower()}-primary", "version": "1.0.0",
            "created_at": "2026-02-15T00:00:00Z", "author_ref": "study-methods-group",
            "prespecification_cutoff": {"cutoff_type": "before_first_enrollment", "cutoff_time": "2026-03-01T00:00:00Z"},
            "metric_name": name,
            "formal_definition": {"numerator": f"{name} numerator per Section 8.2",
                                  "denominator": f"{name} denominator per Section 8.2",
                                  "exclusions": ["indeterminate adjudication", "commensurability ineligible", "binary projection excluded"],
                                  "executable": executable(rid)},
            "binary_validity_required": True,
            "validity_dimension_spec": {"mode": "binary", "executable": executable("pe-binary-v1")},
            "commensurability": {"same_answer_space_required": True},
            "alignment_relation": executable("alignment-same-v1"),
            "aggregation_and_uncertainty": {"estimator": executable("binomial-point-v1"),
                                            "min_cell_size": 1, "interval_method": "Wilson"},
        })

    metrics = {n: metric_artifact(n, f"{n.lower()}-v1") for n in ("RAIR", "RSR", "EAR")}
    plan = mk({
        "artifact_kind": "analysis_plan", "artifact_id": "https://example.org/dses/plans/pe-primary", "version": "1.0.0",
        "created_at": "2026-02-15T00:00:00Z", "author_ref": "study-methods-group",
        "prespecification_cutoff": {"cutoff_type": "before_first_enrollment", "cutoff_time": "2026-03-01T00:00:00Z"},
        "primary_metric_ref": aref(metrics["RAIR"]),
        "primary_evaluation_criterion_ref": aref(criterion),
        "primary_population": "Membership-committed eligible cases with a commensurable primary projection and a determinate adjudication.",
        "primary_projection_rule_ref": aref(projection),
        "disclosure_commitments": True,
    })
    cohort = mk({
        "artifact_kind": "cohort_definition", "artifact_id": "https://example.org/dses/cohorts/pe-ed-2026", "version": "1.0.0",
        "created_at": "2026-02-15T00:00:00Z", "author_ref": "study-methods-group",
        "prespecification_cutoff": {"cutoff_type": "before_first_enrollment", "cutoff_time": "2026-03-01T00:00:00Z"},
        "eligibility_rule": {"inclusion": [{"description": "ED encounter with CTPA ordered or considered",
                                            "code_sets": [{"system": "SNOMED CT", "system_version": "2026-03-01", "codes": ["241541005"]}]}],
                             "exclusion": [{"description": "Age under 18",
                                            "code_sets": [{"system": "local", "system_version": "1", "codes": ["age-lt-18"]}]}],
                             "executable": executable("pe-eligibility-v1")},
        "workflow_refs": ["ed-cta-workflow-v3"],
        "enrollment_window": {"start": "2026-03-01T00:00:00Z", "end": "2026-04-30T23:59:59Z"},
        "expected_source_systems": ["ed-information-system", "radiology-information-system"],
        "sampling_scheme": {"scheme": "census"}, "manifest_membership": True,
        "manifest_cadence": {"max_interval": "P31D", "max_latency_after_period_end": "P2D"},
        "membership_multiplicity": "unique_decision_instance",
        "checkpoint_policy": {"observation_scope": "all_tracks", "max_interval": "P100D"},
        "unit_of_analysis": "individual_clinician",
        "evaluation_criteria": {"primary": aref(criterion), "additional": []},
        "analysis_plan_ref": aref(plan),
    })
    governance = mk({
        "artifact_kind": "secondary_use_governance",
        "artifact_id": "https://example.org/dses/governance/pe-reader-review-2026",
        "version": "1.0.0", "created_at": "2026-02-15T00:00:00Z", "author_ref": "study-methods-group",
        "prespecification_cutoff": {"cutoff_type": "before_first_enrollment", "cutoff_time": "2026-03-01T00:00:00Z"},
        "purpose": "Departmental quality improvement review of AI reliance behaviour, reported to the reader "
                   "and the quality committee. Not a credentialing or employment process.",
        "purpose_code": "quality_improvement",
        "governance_timing": "prospective",
        "privacy_basis": {"patient_data_basis": "hipaa_operations", "professional_identity_mode": "pseudonymous", "identity_binding_holder": "departmental-quality-committee"},
        "decision_consequence": "advisory",
        "authorized_recipients": ["subject-reader", "departmental-quality-committee"],
        "review_body": "departmental-quality-committee",
        "max_observation_window_days": 180,
        "min_cell_size": 2,
        "case_mix_adjustment": {"required": True, "method_ref": "pe-case-mix-v1"},
        "subject_notification": "The reader is notified before derivation and receives the artifact and its "
                                "balanced context at the same time as the committee.",
        "appeal_pathway": "Written appeal to the quality committee within 30 days, with case-level review.",
        "retention": "Destroyed 24 months after derivation.",
        "high_stakes_safeguards": {
            "aggregate_metric_sole_basis_prohibited": True,
            "case_level_review_required": True,
            "subject_access_to_evidence": True,
            "appeal_available": True,
            "subject_notification_required": True,
        },
    })
    assignments = mk({
        "artifact_kind": "responsibility_assignments",
        "artifact_id": "https://example.org/dses/assignments/pe-2026",
        "version": "1.0.0", "created_at": "2026-02-20T00:00:00Z", "author_ref": "study-methods-group",
        "prespecification_cutoff": {"cutoff_type": "before_first_enrollment", "cutoff_time": "2026-03-01T00:00:00Z"},
        "assignment_source": "credentialed_workflow_directory",
        "assignments": [
            {"case_ref": f"case-chain-{c}", "subject_ref": (SUBJECT if c in SUBJECT_CASES else f"clinician-{c}"),
             "role": "responsible_decision_maker", "decision_time": "2026-03-10T03:00:00Z"}
            for c in [f"c{i:02d}" for i in range(12)]
        ],
    })
    artifacts = {"cohort_definition": cohort, "secondary_use_governance": governance,
                 "responsibility_assignments": assignments, "evaluation_criterion": criterion, "adjudication_charter": charter,
                 "analysis_plan": plan, "projection_rule": projection}
    for n, m in metrics.items():
        artifacts[f"metric_definition_{n.lower()}"] = m
    for name, art in artifacts.items():
        json.dump(art, open(os.path.join(ROOT, "artifacts", f"{name}.json"), "w"), indent=2)

    engine_digest = digest_obj(file_digest(os.path.join(ROOT, "scripts", "dses_derivation.py")))
    engine_located = {"media_type": "text/x-python", "locator": "scripts/dses_derivation.py",
                      "digest": engine_digest}

    coh = Chain("cohort", COHORT)
    coh.add("cohort_chain_created", {"cohort_definition_ref": aref(cohort), "analysis_plan_ref": aref(plan),
                                     "definition_set": [aref(x) for x in artifacts.values()],
                                     "declared_integrity_class": "I2", "key_directory": key_directory},
            "2026-03-01T00:00:00Z")

    def anchor(target_hash, artifact_id, version, when, kind):
        body = anchor_receipt_body(target_hash, when, "anchor-authority-01")
        receipt = sign_dses(anchor_key, "anchor-authority-01-key-1", "anchor-receipt", anchor_receipt_target(body))
        coh.add("anchor_evidence_recorded", {"target_kind": kind, "artifact_id": artifact_id, "artifact_version": version,
                                             "artifact_hash": target_hash, "anchor_profile": "DSES-ANCHOR-v1",
                                             "receipt_body": body, "receipt_signature": receipt}, when)

    for art in artifacts.values():
        anchor(art["content_hash"], art["artifact_id"], art["version"], "2026-02-16T09:00:00Z", "definition_artifact")

    # -------- two eligibility manifests, each a separate membership tree --------
    manifest_groups = [[c[0] for c in CASES if c[8] == 0], [c[0] for c in CASES if c[8] == 1]]
    manifest_meta, all_tokens = [], {}
    periods = [("2026-03-01T00:00:00Z", "2026-03-31T23:59:59Z", "2026-04-02T00:00:00Z"),
               ("2026-04-01T00:00:00Z", "2026-04-30T23:59:59Z", "2026-05-02T00:00:00Z")]
    for gi, group in enumerate(manifest_groups):
        tokens = [f"hmac-token-{c}" for c in group]
        leaves = [t.encode() for t in tokens]
        root = mth(leaves).hex()
        start, end, when = periods[gi]
        mp = {"period_start": start, "period_end": end, "manifest_count": len(tokens),
              "eligible_case_commitment_root": root, "membership_tree_size": len(tokens),
              "membership_token_scheme": "hmac-sha256-per-decision-instance-v1",
              "membership_leaf_encoding": "utf8_membership_token",
              "membership_multiplicity": "unique_decision_instance",
              "source_census_ref": f"ed-volume-{start[:7]}", "reconciliation_status": "reconciled",
              "attesting_system": "ed-information-system"}
        mp["attestation_signature"] = sign_dses(ed_key, "ed-information-system-key-1", "eligibility-manifest", h(canon(mp)))
        ev = coh.add("eligibility_manifest_committed", mp, when)
        manifest_meta.append({"event_hash": ev["integrity"]["event_hash"], "root": root, "leaves": leaves, "tokens": tokens})
        for i, c in enumerate(group):
            all_tokens[c] = (gi, i, tokens[i])

    tracks, seqs, adj_hash, index_time = [], {}, {}, {}
    for case, baseline, ai, ev_state, conclusion, status, expo, link, mgroup in CASES:
        gi, li, token = all_tokens[case]
        mm = manifest_meta[gi]
        t = Chain("case", f"case-chain-{case}")
        t.add("case_track_created", {"membership_leaf": token, "membership_leaf_encoding": "utf8_membership_token",
                                     "manifest_ref": mm["event_hash"],
                                     "manifest_inclusion_proof": {"construction": "rfc9162_sha256", "root": mm["root"],
                                                                  "tree_size": len(mm["leaves"]), "leaf_index": li,
                                                                  "audit_path": [x.hex() for x in inclusion_path(li, mm["leaves"])]}},
              "2026-05-02T00:05:00Z")
        if link == "decision_record_missing":
            t.add("linkage_attempted", {"attempt_method": "ttp_deterministic", "attempt_result": "decision_record_missing",
                                        "attempt_detail": "No instrumented v0.1 decision chain exists; workflow bypassed."},
                  "2026-05-02T00:10:00Z")
            tracks.append(t)
            continue
        dch, fin = build_decision_sequence(case, baseline, ai, ev_state, expo)
        seqs[case] = dch
        index_time[case] = fin["occurred_at"]
        json.dump({"dses_version": "0.1.0", "chain_ref": dch.ref, "events": dch.events},
                  open(os.path.join(ROOT, "examples", "decision-sequences", f"{dch.ref}.json"), "w"), indent=2)
        t.add("linkage_attempted", {"attempt_method": "ttp_deterministic", "attempt_result": "linked",
                                    "attempt_detail": "Honest-broker crosswalk returned a unique match."}, "2026-05-02T00:10:00Z")
        t.add("linkage_asserted", {
            "decision_sequence_ref": {"dses_version": "0.1.0", "sequence_head_hash": dch.prev,
                                      "final_decision_hash": fin["integrity"]["event_hash"],
                                      "resolver": f"examples/decision-sequences/{dch.ref}.json",
                                      "declared_integrity_class": "I2"},
            "linkage_token_method": "ttp_deterministic",
            "linkage_security": {"method": "ttp_deterministic", "ttp_identity": "institutional-honest-broker",
                                 "ttp_governance_ref": "broker-charter-2026", "crosswalk_location": "on_premises",
                                 "threat_model_note": "Broker trusted for identity resolution; broker compromise defeats pseudonymity."},
            "crosswalk_custodian": "institutional-honest-broker",
            "planned_evaluation_criterion_ref": aref(criterion),
            "linkage_accuracy": {"linkage_method": "deterministic", "linkage_validation_status": "validated",
                                 "linkage_validation_ref": "broker-validation-2026Q1", "estimated_false_match_rate": 0.001,
                                 "estimated_false_nonmatch_rate": 0.004, "linkage_algorithm_version": "broker-link-2.4.1"},
        }, "2026-05-02T00:11:00Z")
        t.add("linkage_status_updated", {"followup_state": "active",
                                         "criterion_states": [{"evaluation_criterion_ref": aref(criterion),
                                                               "maturation_state": "pending", "adjudication_state": "not_started",
                                                               "risk_window": "P90D"}],
                                         "index_date_ref": fin["integrity"]["event_hash"],
                                         "data_availability_cutoff": "2026-05-01T00:00:00Z"}, "2026-05-02T00:12:00Z")
        tracks.append(t)

    log = [canon(t.head_obs(1)) for t in tracks]
    ck1_root = mth(log).hex()
    ck1 = coh.add("checkpoint_committed", {"construction": "rfc9162_sha256", "checkpoint_epoch": 1,
                                           "log_kind": "append_only_head_observation_log", "checkpoint_log_root": ck1_root,
                                           "checkpoint_log_size": len(log), "leaf_encoding": "rfc8785_head_observation",
                                           "head_observations": [t.head_obs(1) for t in tracks],
                                           "coverage": {"eligible_track_count": len(tracks), "observed_track_count": len(tracks),
                                                        "missing_track_refs": []}}, "2026-05-03T00:00:00Z")
    anchor(ck1["integrity"]["event_hash"], "urn:dses:checkpoint:1", "1", "2026-05-03T00:05:00Z", "checkpoint_event")

    for case, baseline, ai, ev_state, conclusion, status, expo, link, mgroup in CASES:
        if link not in ("linked", "immature"):
            continue
        t = tracks[[c[0] for c in CASES].index(case)]
        t.add("outcome_observed", {
            "observed_fact": {"description": "90-day composite outcome ascertained", "code_system": "SNOMED CT",
                              "code_system_version": "2026-03-01", "code": "473231009", "value": "ascertained"},
            "observation_date": "2026-06-19T00:00:00Z",
            "evidence_source": {"category": "chart_abstraction", "reference": f"abstraction-{case}",
                                "content_hash": h(f"abstraction-{case}".encode()),
                                "provenance": {"source_authenticity": "authenticated EHR export",
                                               "source_immutability": "vendor audit log only", "source_signature": "absent",
                                               "source_timestamp_assurance": "EHR server clock", "source_revision_history": "available"}},
            "observability_determinants": [{"mechanism": "unconditional"}],
            "intervening_events": [],
        }, "2026-06-20T00:00:00Z")
        if link == "immature":
            t.add("linkage_status_updated", {"followup_state": "active",
                                             "criterion_states": [{"evaluation_criterion_ref": aref(criterion),
                                                                   "maturation_state": "pending", "adjudication_state": "not_started",
                                                                   "risk_window": "P90D"}],
                                             "index_date_ref": seqs[case].events[-1]["integrity"]["event_hash"],
                                             "data_availability_cutoff": "2026-06-01T00:00:00Z"}, "2026-06-20T01:00:00Z")
            continue
        refs = []
        for adj, when in (("adj-A", "2026-07-01T14:00:00Z"), ("adj-B", "2026-07-01T16:00:00Z")):
            assessment = ({"assessable": True, "conclusion": conclusion} if status == "determinate"
                          else {"assessable": False, "inability_reason": "Treated course without confirmatory imaging."})
            e = t.add("adjudicator_assessment_committed", {
                "adjudicator_ref": adj,
                "packet_manifest": [{"evidence_category": "index_imaging_deidentified", "content_hash": h(f"img-{case}".encode())},
                                    {"evidence_category": "clinical_course_abstract", "content_hash": h(f"course-{case}".encode())}],
                "blinding_planned": ["ai_output", "post_ai_documentation", "co_adjudicator_conclusions"],
                "blinding_actual": ["ai_output", "post_ai_documentation", "co_adjudicator_conclusions"],
                "blinding_breach": False, "assessment": assessment, "certainty": "moderate",
                "pre_consensus": True, "charter_ref": aref(charter),
            }, when, hiding=True, nonces=nonces, actor={"actor_ref": adj, "actor_type": "human", "role": "adjudicator"})
            refs.append(e["integrity"]["event_hash"])
        p = {"evaluation_criterion_ref": aref(criterion), "charter_ref": aref(charter), "assessment_refs": refs,
             "resolution_process": {"method": "consensus", "procedure_ref": "charter-sec-6"},
             "conclusion_status": status, "process_flags": [],
             "inter_adjudicator_agreement": {"statistic": "percent_agreement_pre_consensus", "value": 1,
                                             "computed_over_pre_consensus_only": True},
             "time_to_adjudication": "P103D"}
        if status == "determinate":
            p["conclusion"] = conclusion
        e = t.add("reference_standard_adjudicated", p, "2026-07-02T10:00:00Z", hiding=True, nonces=nonces)
        adj_hash[case] = e["integrity"]["event_hash"]
        t.add("linkage_status_updated", {"followup_state": "active",
                                         "criterion_states": [{"evaluation_criterion_ref": aref(criterion),
                                                               "maturation_state": "mature", "adjudication_state": "concluded",
                                                               "risk_window": "P90D"}],
                                         "index_date_ref": seqs[case].events[-1]["integrity"]["event_hash"],
                                         "data_availability_cutoff": "2026-06-19T00:00:00Z"}, "2026-07-02T10:01:00Z")

    log += [canon(t.head_obs(2)) for t in tracks]
    ck2_root = mth(log).hex()
    ck2 = coh.add("checkpoint_committed", {"construction": "rfc9162_sha256", "checkpoint_epoch": 2,
                                           "log_kind": "append_only_head_observation_log", "checkpoint_log_root": ck2_root,
                                           "checkpoint_log_size": len(log), "leaf_encoding": "rfc8785_head_observation",
                                           "head_observations": [t.head_obs(2) for t in tracks],
                                           "coverage": {"eligible_track_count": len(tracks), "observed_track_count": len(tracks),
                                                        "missing_track_refs": []},
                                           "consistency_proof": {"previous_epoch": 1, "previous_root": ck1_root,
                                                                 "previous_size": len(tracks),
                                                                 "path": [x.hex() for x in consistency_path(len(tracks), log)]}},
                  "2026-07-03T00:00:00Z")
    anchor(ck2["integrity"]["event_hash"], "urn:dses:checkpoint:2", "2", "2026-07-03T00:05:00Z", "checkpoint_event")
    coh.add("key_rotated", {"retired_key_ref": "outcome-registry-01-key-1", "successor_key_ref": "outcome-registry-01-key-2",
                            "effective_at": "2026-07-01T00:00:00Z", "reason": "scheduled_rotation"}, "2026-07-03T01:00:00Z")

    sys.path.insert(0, RULES)
    import pe_binary_v1  # noqa: E402
    import binomial_point_v1  # noqa: E402
    import alignment_same_v1  # noqa: E402
    import pe_projection_v1  # noqa: E402
    import rair_v1  # noqa: E402
    import rsr_v1  # noqa: E402
    import ear_v1  # noqa: E402
    RULEMODS = {"rair-v1": rair_v1, "rsr-v1": rsr_v1, "ear-v1": ear_v1}

    concl_at = {c: (concl, st) for c, _, _, _, concl, st, _, link, _ in CASES if link == "linked"}
    derived_files = []

    def compute(rule_id, active_concl, current_adj):
        """Compute metrics through the shipped derivation engine and rule modules."""
        records = []
        for case in sorted(seqs):
            if case not in active_concl:  # linked but immature: no adjudication yet
                continue
            concl, st = active_concl[case]
            records.append({
                "case_ref": case,
                "trajectory": pe_projection_v1.project(seqs[case].events),
                "conclusion_status": st,
                "conclusion": concl,
                "adjudication_hash": current_adj[case],
            })
        n, d, used_hashes, excl = recompute_metric(records, pe_binary_v1, RULEMODS[rule_id], alignment_same_v1)
        used = [case for case in sorted(seqs) if case in current_adj and current_adj[case] in set(used_hashes)]
        return n, d, used, excl

    def emit(tag, when, active_concl, current_adj):
        pop_tuples = [{"case_ref": t.ref, "chain_ref": t.ref, "case_chain_head": t.prev, "case_chain_sequence": t.seq - 1}
                      for t in tracks]
        snap = coh.add("analysis_snapshot_committed", {
            "as_of_time": when, "cohort_chain_head_before_snapshot": coh.prev,
            "population_commitment": {"construction": "rfc9162_sha256", "root": mth([canon(x) for x in pop_tuples]).hex(),
                                      "tree_size": len(pop_tuples), "leaf_encoding": "rfc8785_population_tuple"},
            "population_tuples": pop_tuples,
            "definition_versions": [aref(x) for x in artifacts.values()],
            "software_digest": engine_digest,
        }, when)
        sref = snap["integrity"]["event_hash"]
        linked_n = sum(1 for c in CASES if c[7] in ("linked", "immature"))
        mature_n = sum(1 for c in CASES if c[7] == "linked")
        counts = {"membership_committed_population": len(CASES), "tracked": len(tracks),
                  "linked": linked_n,
                  "linkage_failed": sum(1 for c in CASES if c[7] == "decision_record_missing"),
                  "linkage_ambiguous": 0,
                  "pending_maturation": sum(1 for c in CASES if c[7] == "immature"),
                  "mature": mature_n,
                  "concluded_determinate": sum(1 for c in CASES if c[7] == "linked" and c[5] == "determinate"),
                  "conclusion_status_breakdown": {"determinate": sum(1 for c in CASES if c[7] == "linked" and c[5] == "determinate"),
                                                  "indeterminate": sum(1 for c in CASES if c[7] == "linked" and c[5] == "indeterminate")},
                  "followup_state_breakdown": {"active": linked_n}}
        blinding = {"blinded_committed": mature_n, "blinded": 0, "unblinded_or_breached": 0}
        for name in ("RAIR", "RSR", "EAR"):
            rid = f"{name.lower()}-v1"
            n, d, used, excl = compute(rid, active_concl, current_adj)
            art = {
                "artifact_type": "reliance_metric_derived", "artifact_id": f"urn:dses:derived:{name.lower()}-{tag}",
                "derived_at": when, "metric_definition_ref": aref(metrics[name]),
                "projection_set": {"mode": "inline", "input_event_hashes": sorted(current_adj[c] for c in used)},
                "numerator": n, "denominator": d, "value": None if d == 0 else n / d,
                "disclosures": {
                    "completeness_accounting": counts,
                    "verification_rule": "OL-ADJUDICATED",
                    "blinding_breakdown": blinding,
                    "primary_evaluation_criterion": True, "criterion_validation_present": False,
                    "commensurability_exclusions": excl["commensurability"],
                    "binary_projection_exclusions": {"indeterminate": excl["indeterminate"],
                                                     "partially_correct": excl["partially_correct"],
                                                     "not_classifiable": excl["not_classifiable"]},
                    "plan_reference": {"analysis_plan_ref": aref(plan)},
                },
                "recomputability": {"analysis_snapshot_ref": sref,
                                    "definition_hashes": [aref(metrics[name]), aref(criterion), aref(projection)],
                                    "derivation_software_digest": engine_located, "canonicalization": "RFC8785",
                                    "input_artifact_availability": {"available": len(used), "archived": 0, "unavailable": 0}},
                "unit_of_analysis": "cohort",
                "inclusion_filters": ["membership_committed", "linked", "mature", "primary_criterion",
                                      "commensurable", "binary_projectable"],
            }
            if d > 0:
                art["interval"] = binomial_point_v1.interval(n, d)
            art["artifact_hash"] = artifact_content_hash(art)
            fn = f"derived-{name.lower()}-{tag}.json"
            json.dump(art, open(os.path.join(ROOT, "examples", "derived", fn), "w"), indent=2)
            derived_files.append((fn, art["artifact_id"]))
            coh.add("derived_artifact_registered", {"derived_artifact_id": art["artifact_id"],
                                                    "derived_artifact_hash": art["artifact_hash"],
                                                    "artifact_type": "reliance_metric_derived", "analysis_snapshot_ref": sref,
                                                    "depends_on_event_hashes": art["projection_set"]["input_event_hashes"]}, when)
            print(f"  {tag} {name}: {n}/{d}  exclusions {excl}")
        return sref, counts, blinding


    def emit_individual(when, active_concl, current_adj, sref, counts, blinding):
        """One reader, one bounded window, under governance.

        Every count here is recomputed by the verifier from snapshot-frozen
        evidence; nothing in this artifact is asserted. The point of shipping it
        is that a per-reader rate cannot be displayed without the context that
        conditions it.
        """
        window = {"start": "2026-03-01T00:00:00Z", "end": "2026-06-30T23:59:59Z"}
        assigned = [a for a in assignments["assignments"]
                    if a["subject_ref"] == SUBJECT
                    and window["start"] <= a["decision_time"] <= window["end"]]
        recs = []
        for a in assigned:
            case = a["case_ref"].replace("case-chain-", "")
            if case in seqs and case in active_concl:
                proj = pe_projection_v1.project(seqs[case].events)
                if proj is not None and "excluded" not in proj \
                        and proj.get("baseline_actor") == SUBJECT and proj.get("evaluation_actor") == SUBJECT:
                    concl, st = active_concl[case]
                    recs.append({"case": case, "trajectory": proj, "conclusion": concl,
                                 "conclusion_status": st, "adjudication_hash": current_adj[case]})

        link_state = {}
        mat_state = {}
        for c in CASES:
            link_state[c[0]] = c[7]
            mat_state[c[0]] = ("mature" if c[7] == "linked" else
                               "pending" if c[7] == "immature" else "not_applicable")
        linkage_bd = dict(sorted(Counter(
            ("linked" if link_state.get(a["case_ref"].replace("case-chain-", "")) in ("linked", "immature")
             else link_state.get(a["case_ref"].replace("case-chain-", ""), "unknown")) for a in assigned).items()))
        maturation_bd = dict(sorted(Counter(
            mat_state.get(a["case_ref"].replace("case-chain-", ""), "unknown") for a in assigned).items()))
        adj_bd = {"determinate": 0, "indeterminate": 0, "not_adjudicated": 0}
        for a in assigned:
            case = a["case_ref"].replace("case-chain-", "")
            if case in active_concl:
                adj_bd[active_concl[case][1]] = adj_bd.get(active_concl[case][1], 0) + 1
            else:
                adj_bd["not_adjudicated"] += 1

        def vbreak(which):
            out = {"correct": 0, "incorrect": 0, "excluded": 0}
            for rec in recs:
                if rec["conclusion_status"] != "determinate":
                    out["excluded"] += 1
                    continue
                b = pe_binary_v1.binary(pe_binary_v1.classify(rec["trajectory"][which], rec["conclusion"]))
                out["correct" if b == "correct" else "incorrect" if b == "incorrect" else "excluded"] += 1
            return out

        context = {
            "subject_decision_instance_count": len(assigned),
            "assignment_ref": aref(assignments),
            "linkage_breakdown": linkage_bd,
            "maturation_breakdown": maturation_bd,
            "adjudication_breakdown": {k: v for k, v in sorted(adj_bd.items())},
            "metric_eligible_count": len(recs),
            "subject_case_count": len(recs),
            "adjudication_status_breakdown": dict(sorted(Counter(r["conclusion_status"] for r in recs).items())),
            "commensurability_breakdown": {
                "commensurable": sum(bool(r["trajectory"].get("commensurable")) for r in recs),
                "noncommensurable": sum(not bool(r["trajectory"].get("commensurable")) for r in recs)},
            "baseline_validity_breakdown": vbreak("baseline"),
            "ai_validity_breakdown": vbreak("ai"),
            "evaluation_validity_breakdown": vbreak("evaluation"),
            "ai_system_breakdown": dict(sorted(Counter(r["trajectory"].get("ai_system_ref", "UNKNOWN") for r in recs).items())),
            "exposure_class_breakdown": dict(sorted(Counter(r["trajectory"].get("exposure_class", "UNKNOWN") for r in recs).items())),
            "index_period_breakdown": dict(sorted(Counter(a["decision_time"][:7] for a in assigned).items())),
        }

        records = [{"case_ref": r["case"], "trajectory": r["trajectory"], "conclusion": r["conclusion"],
                    "conclusion_status": r["conclusion_status"], "adjudication_hash": r["adjudication_hash"]}
                   for r in recs]
        n, d, used, excl = recompute_metric(records, pe_binary_v1, RULEMODS["rair-v1"], alignment_same_v1)
        art = {
            "artifact_type": "reliance_metric_derived",
            "artifact_id": "urn:dses:derived:rair-subject-0417-v1",
            "derived_at": when, "metric_definition_ref": aref(metrics["RAIR"]),
            "projection_set": {"mode": "inline", "input_event_hashes": sorted(used)},
            "numerator": n, "denominator": d, "value": None if d == 0 else n / d,
            "unit_of_analysis": "individual_clinician",
            "subject_ref": SUBJECT,
            "governance_ref": aref(governance),
            "observation_window": window,
            "reliance_context": context,
            "case_mix_disclosure": {"method_ref": "pe-case-mix-v1", "adjusted": True,
                                    "covariates": ["pretest_probability", "study_quality", "shift_load"]},
            "disclosures": {
                "completeness_accounting": counts,
                "verification_rule": "OL-ADJUDICATED",
                "blinding_breakdown": blinding,
                "primary_evaluation_criterion": True, "criterion_validation_present": False,
                "commensurability_exclusions": excl["commensurability"],
                "binary_projection_exclusions": {"indeterminate": excl["indeterminate"],
                                                 "partially_correct": excl["partially_correct"],
                                                 "not_classifiable": excl["not_classifiable"]},
                "plan_reference": {"analysis_plan_ref": aref(plan)},
            },
            "recomputability": {"analysis_snapshot_ref": sref,
                                "definition_hashes": [aref(metrics["RAIR"]), aref(criterion), aref(projection)],
                                "derivation_software_digest": engine_located, "canonicalization": "RFC8785",
                                "input_artifact_availability": {"available": len(used), "archived": 0, "unavailable": 0}},
            "inclusion_filters": ["membership_committed", "linked", "mature", "primary_criterion",
                                  "commensurable", "binary_projectable", "subject_scoped", "window_bounded"],
        }
        if d > 0:
            art["interval"] = binomial_point_v1.interval(n, d)
        art["artifact_hash"] = artifact_content_hash(art)
        fn = "derived-rair-subject-0417-v1.json"
        json.dump(art, open(os.path.join(ROOT, "examples", "derived", fn), "w"), indent=2)
        derived_files.append((fn, art["artifact_id"]))
        coh.add("derived_artifact_registered", {"derived_artifact_id": art["artifact_id"],
                                                "derived_artifact_hash": art["artifact_hash"],
                                                "artifact_type": "reliance_metric_derived",
                                                "analysis_snapshot_ref": sref,
                                                "depends_on_event_hashes": art["projection_set"]["input_event_hashes"]}, when)
        print(f"  individual RAIR for {SUBJECT}: {n}/{d} over {len(recs)} subject cases; context {context['ai_validity_breakdown']}")

    emit("v1", "2026-07-04T00:00:00Z", dict(concl_at), dict(adj_hash))
    v1_ids = [aid for _, aid in derived_files]

    t = tracks[[c[0] for c in CASES].index("c02")]
    rev = t.add("reference_standard_adjudicated", {
        "evaluation_criterion_ref": aref(criterion),
        "resolution_process": {"method": "chair_ruling", "procedure_ref": "charter-sec-7"},
        "conclusion_status": "determinate", "conclusion": "negative", "process_flags": [],
        "charter_ref": aref(charter), "deciding_adjudicator_ref": "adj-C",
        "time_to_adjudication": "P160D", "revises_event_hash": adj_hash["c02"], "revision_reason": "new_evidence",
        "revision_reason_description": "Delayed pathology contradicted the original composite determination.",
    }, "2026-08-10T10:00:00Z", hiding=True, nonces=nonces)
    for aid in v1_ids:
        coh.add("derived_artifact_superseded", {"derived_artifact_id": aid, "reason": "adjudication_revised",
                                                "detail": "Adjudication for c02 revised; recomputation issued as v2."},
                "2026-08-10T11:00:00Z")
    concl_v2 = dict(concl_at)
    concl_v2["c02"] = ("negative", "determinate")
    adj_v2 = dict(adj_hash)
    adj_v2["c02"] = rev["integrity"]["event_hash"]

    log += [canon(t2.head_obs(3)) for t2 in tracks]
    ck3 = coh.add("checkpoint_committed", {"construction": "rfc9162_sha256", "checkpoint_epoch": 3,
                                           "log_kind": "append_only_head_observation_log", "checkpoint_log_root": mth(log).hex(),
                                           "checkpoint_log_size": len(log), "leaf_encoding": "rfc8785_head_observation",
                                           "head_observations": [t2.head_obs(3) for t2 in tracks],
                                           "coverage": {"eligible_track_count": len(tracks), "observed_track_count": len(tracks),
                                                        "missing_track_refs": []},
                                           "consistency_proof": {"previous_epoch": 2, "previous_root": ck2_root,
                                                                 "previous_size": 2 * len(tracks),
                                                                 "path": [x.hex() for x in consistency_path(2 * len(tracks), log)]}},
                  "2026-08-11T00:00:00Z")
    anchor(ck3["integrity"]["event_hash"], "urn:dses:checkpoint:3", "3", "2026-08-11T00:05:00Z", "checkpoint_event")

    sref2, counts2, blinding2 = emit("v2", "2026-08-12T00:00:00Z", concl_v2, adj_v2)
    emit_individual("2026-08-12T01:00:00Z", concl_v2, adj_v2, sref2, counts2, blinding2)
    coh.add("outcome_integrity_event", {"kind": "verification_performed",
                                        "detail": "Full package verification by the deploying operator."}, "2026-08-12T02:00:00Z")

    export_sig = sign_dses(keys["outcome-registry-01-key-2"]["private"], "outcome-registry-01-key-2", "export-head", coh.prev)

    out = {"package": "DSES v0.2.0-rc3 worked example",
           "description": "Twelve membership-committed eligible cases across two periodic manifests, resolvable v0.1 decision sequences with verified payload commitments, reliance metrics recomputed by executing the declared rule artifacts against snapshot-frozen evidence, an adjudication revision with metric supersession, externally rooted anchor receipts, and key rotation. No label in this package is stored where it can be derived.",
           "cohort_chain": coh.events, "case_chains": [t2.events for t2 in tracks],
           "export_head_signature": export_sig}
    json.dump(out, open(os.path.join(ROOT, "examples", "example-package.json"), "w"), indent=2)
    json.dump({"note": "Nonce store for randomized hiding commitments; colocated with payloads, destroyed with them.",
               "scheme": "random-128-bit-per-commitment", "nonces": nonces},
              open(os.path.join(ROOT, "examples", "nonce-store.json"), "w"), indent=2)
    print("generated example-package.json, anchor-trust-store.json, artifacts/, decision-sequences/, derived/")


if __name__ == "__main__":
    build()
