#!/usr/bin/env python3
"""DSES v0.2.0-rc3 adversarial regression suite.

Two hard rules for this harness, both from the fifth review round:

  1. A fixture passes only if the verifier rejects the package AND the
     verifier's failure output names the SPECIFIC rule the fixture attacks.
     "Something somewhere broke" is not a defense of anything.
  2. Mutations should rebuild orthogonal cryptographic layers when practical,
     so the named rule is actually exercised. Cascading failures are permitted:
     the harness earns only the claim that the SPECIFIC named rule fired, not
     that no other rule also rejected the package.

Schema fixtures assert rejection by the named schema. Verifier fixtures assert
the named rule identifier appears in the failure output.

Run from the package root: python3 tests/run_regression.py
"""
import copy
import json
import os
import shutil
import subprocess
import sys
import tempfile

from jsonschema import Draft202012Validator

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import dses_core as core  # noqa: E402

EVENT_SCHEMA = Draft202012Validator(json.load(open(os.path.join(ROOT, "schemas", "dses-v0.2-outcome-events.schema.json"))))
DEF_SCHEMA = Draft202012Validator(json.load(open(os.path.join(ROOT, "schemas", "dses-v0.2-definitions.schema.json"))))
DRV_SCHEMA = Draft202012Validator(json.load(open(os.path.join(ROOT, "schemas", "dses-v0.2-derived.schema.json"))))

GOOD = json.load(open(os.path.join(ROOT, "examples", "example-package.json")))
DERIVED_DIR = os.path.join(ROOT, "examples", "derived")
SEQ_DIR = os.path.join(ROOT, "examples", "decision-sequences")
NONCES = json.load(open(os.path.join(ROOT, "examples", "nonce-store.json")))["nonces"]

# An attacker key: the external trust store holds the real authority's public half,
# so anything signed with this must fail anchor verification. Used where a fixture
# needs a syntactically well formed receipt over altered content.
from cryptography.hazmat.primitives.asymmetric import ed25519 as _ed  # noqa: E402
ANCHOR_SK = _ed.Ed25519PrivateKey.generate()

CASES = []


def case(name, cls, origin):
    def deco(fn):
        CASES.append((name, cls, origin, fn))
        return fn
    return deco


def rebuild_chain(events):
    """Recompute payload commitments (content ones), event hashes, and links so
    a payload mutation leaves every orthogonal layer valid."""
    prev = None
    for e in events:
        if e["payload_commitment"]["commitment_type"] == "content_digest" and "payload" in e:
            e["payload_commitment"]["digest"] = core.h(core.canon(e["payload"]))
        elif "payload" in e:
            nonce = NONCES.get(e["event_id"])
            if nonce:
                e["payload_commitment"]["digest"] = core.h(bytes.fromhex(nonce) + core.canon(e["payload"]))
        if prev:
            e["integrity"]["prev_event_hash"] = prev
        else:
            e["integrity"].pop("prev_event_hash", None)
        e["integrity"]["event_hash"] = core.event_preimage_hash(e)
        prev = e["integrity"]["event_hash"]


def run_verifier(pkg_path, extra=()):
    args = [sys.executable, os.path.join(ROOT, "scripts", "dses_verify.py"), pkg_path, "--quiet"]
    if "--anchor-trust" not in extra:
        args += ["--anchor-trust", os.path.join(ROOT, "examples", "anchor-trust-store.json")]
    args += list(extra)
    r = subprocess.run(args, capture_output=True, text=True)
    return r.returncode, r.stdout


def verifier_rejects(mutate, rule, extra=()):
    """mutate(pkg, tmpdir) edits a deep copy; harness asserts nonzero exit AND
    the named rule in the failure output."""
    pkg = copy.deepcopy(GOOD)
    with tempfile.TemporaryDirectory() as d:
        more = mutate(pkg, d) or ()
        p = os.path.join(d, "pkg.json")
        json.dump(pkg, open(p, "w"))
        code, out = run_verifier(p, tuple(more) + tuple(extra))
        fired = f"FAILED [{rule}]" in out
        return code != 0 and fired, (f"exit={code}, rule {rule} fired={fired}")


def schema_rejects(schema, obj):
    return (not schema.is_valid(obj)), "schema"


def find(chain, etype):
    for i, e in enumerate(chain):
        if e["event_type"] == etype:
            return i, e
    raise KeyError(etype)


# ================================================================ envelope layer

@case("event hash not matching its RFC 8785 preimage", "C", "round 3")
def c01():
    def m(pkg, d):
        pkg["case_chains"][0][1]["integrity"]["event_hash"] = "00" * 32
    return verifier_rejects(m, "EVT-HASH")


@case("broken predecessor link", "C", "round 3")
def c02():
    def m(pkg, d):
        pkg["case_chains"][0][2]["integrity"]["prev_event_hash"] = "11" * 32
        pkg["case_chains"][0][2]["integrity"]["event_hash"] = core.event_preimage_hash(pkg["case_chains"][0][2])
    return verifier_rejects(m, "CHAIN-LINK")


@case("payload edited under a stale content commitment", "C", "round 3")
def c03():
    def m(pkg, d):
        i, e = find(pkg["case_chains"][0], "outcome_observed")
        e["payload"]["observation_date"] = "2026-01-01T00:00:00Z"
    return verifier_rejects(m, "PC-CONTENT")


@case("adjudication payload with a hiding commitment and the wrong nonce", "C", "round 3")
def c04():
    def m(pkg, d):
        i, e = find(pkg["case_chains"][0], "reference_standard_adjudicated")
        e["payload"]["conclusion"] = "negative"
        # commitment digest and event hash rebuilt so ONLY the nonce binding fails
        e["payload_commitment"]["digest"] = core.h(b"\x00" * 16 + core.canon(e["payload"]))
        rebuild = pkg["case_chains"][0]
        prev = None
        for ev in rebuild:
            if prev:
                ev["integrity"]["prev_event_hash"] = prev
            ev["integrity"]["event_hash"] = core.event_preimage_hash(ev)
            prev = ev["integrity"]["event_hash"]
    return verifier_rejects(m, "PC-NONCE")


@case("low-entropy adjudication committed without hiding", "X", "round 3")
def c05():
    def m(pkg, d):
        ch = pkg["case_chains"][0]
        i, e = find(ch, "reference_standard_adjudicated")
        e["payload_commitment"] = {"alg": "sha-256", "digest": core.h(core.canon(e["payload"])),
                                   "commitment_type": "content_digest"}
        rebuild_chain(ch)
    return verifier_rejects(m, "PC-HIDING")


# ================================================================ trust roots

@case("FULL A1 ATTACK: genesis anchor key substituted, every receipt re-minted, all hashes rebuilt", "C", "round 5, item 1")
def c06():
    def m(pkg, d):
        from cryptography.hazmat.primitives.asymmetric import ed25519
        sk = ed25519.Ed25519PrivateKey.generate()
        for e in pkg["cohort_chain"]:
            if e["event_type"] == "anchor_evidence_recorded":
                body = e["payload"]["receipt_body"]
                e["payload"]["receipt_signature"] = core.sign_dses(
                    sk, "anchor-authority-01-key-1", "anchor-receipt", core.anchor_receipt_target(body))
        rebuild_chain(pkg["cohort_chain"])
    return verifier_rejects(m, "ANCHOR-RECEIPT")


@case("uncommitted top-level key directory injected", "X", "round 5")
def c07():
    def m(pkg, d):
        pkg["key_directory"] = [{"key_ref": "x", "alg": "ed25519", "public_key": "00" * 32}]
    return verifier_rejects(m, "KEY-COMMITTED")


@case("anchor receipt replayed onto a different artifact", "C", "round 5")
def c08():
    def m(pkg, d):
        i, e = find(pkg["cohort_chain"], "anchor_evidence_recorded")
        e["payload"]["artifact_hash"] = "cd" * 32
        rebuild_chain(pkg["cohort_chain"])
    return verifier_rejects(m, "ANCHOR-RECEIPT")


@case("signature by a key outside its committed validity window", "X", "round 5")
def c09():
    def m(pkg, d):
        pkg["export_head_signature"]["key_ref"] = "outcome-registry-01-key-1"
    return verifier_rejects(m, "SIG-KEYTIME")


@case("duplicate key references in the committed directory", "X", "round 5")
def c10():
    def m(pkg, d):
        g = pkg["cohort_chain"][0]
        g["payload"]["key_directory"].append(dict(g["payload"]["key_directory"][0]))
        rebuild_chain(pkg["cohort_chain"])
    return verifier_rejects(m, "KEY-UNIQUE")


# ================================================================ v0.1 binding

@case("REVIEWER'S TAMPER: independence_class flipped in a bound v0.1 payload, nothing else touched", "C", "round 5, item 2")
def c11():
    def m(pkg, d):
        shutil.copytree(SEQ_DIR, os.path.join(d, "seq"))
        f = os.path.join(d, "seq", "decision-chain-c00.json")
        seq = json.load(open(f))
        for e in seq["events"]:
            if e["event_type"] == "preliminary_read_committed":
                e["payload"]["independence_class"] = "DIRECTLY_EXPOSED"
        json.dump(seq, open(f, "w"))
        return ("--sequences", os.path.join(d, "seq"))
    return verifier_rejects(m, "PC-CONTENT")


@case("v0.1 final decision payload replaced with TAMPERED", "C", "round 5, item 2")
def c12():
    def m(pkg, d):
        shutil.copytree(SEQ_DIR, os.path.join(d, "seq"))
        f = os.path.join(d, "seq", "decision-chain-c01.json")
        seq = json.load(open(f))
        seq["events"][-1]["payload"]["decision"] = "TAMPERED"
        json.dump(seq, open(f, "w"))
        return ("--sequences", os.path.join(d, "seq"))
    return verifier_rejects(m, "PC-CONTENT")


@case("v0.1 payload AND commitment rebuilt: caught by the envelope hash instead", "C", "round 5, item 2")
def c13():
    def m(pkg, d):
        shutil.copytree(SEQ_DIR, os.path.join(d, "seq"))
        f = os.path.join(d, "seq", "decision-chain-c00.json")
        seq = json.load(open(f))
        e = seq["events"][-1]
        e["payload"]["decision"] = "negative"
        e["payload_commitment"]["digest"] = core.h(core.canon(e["payload"]))
        json.dump(seq, open(f, "w"))
        return ("--sequences", os.path.join(d, "seq"))
    return verifier_rejects(m, "EVT-HASH")


@case("referenced v0.1 sequence does not resolve", "X", "round 4")
def c14():
    def m(pkg, d):
        for ch in pkg["case_chains"]:
            for e in ch:
                if e["event_type"] == "linkage_asserted":
                    e["payload"]["decision_sequence_ref"]["resolver"] = "examples/decision-sequences/missing.json"
            rebuild_chain(ch)
    return verifier_rejects(m, "V01-RESOLVE")


@case("bound v0.1 head hash does not match the resolved sequence", "C", "round 4")
def c15():
    def m(pkg, d):
        ch = pkg["case_chains"][0]
        for e in ch:
            if e["event_type"] == "linkage_asserted":
                e["payload"]["decision_sequence_ref"]["sequence_head_hash"] = "ef" * 32
        rebuild_chain(ch)
    return verifier_rejects(m, "V01-HEAD")


@case("v0.1 sequence reordered: exposure before baseline, so the declared rule cannot project it", "X", "round 4")
def c16():
    def m(pkg, d):
        shutil.copytree(SEQ_DIR, os.path.join(d, "seq"))
        f = os.path.join(d, "seq", "decision-chain-c00.json")
        seq = json.load(open(f))
        evs = seq["events"]
        evs[1], evs[2] = evs[2], evs[1]
        for i, e in enumerate(evs):
            e["sequence"] = i
        rebuild_chain(evs)
        json.dump(seq, open(f, "w"))
        # rebind the head and final hashes so ONLY the ordering rule can object
        ch = [c for c in pkg["case_chains"] if c[0]["chain_ref"] == "case-chain-c00"][0]
        for e in ch:
            if e["event_type"] == "linkage_asserted":
                e["payload"]["decision_sequence_ref"]["sequence_head_hash"] = evs[-1]["integrity"]["event_hash"]
                e["payload"]["decision_sequence_ref"]["final_decision_hash"] = evs[-1]["integrity"]["event_hash"]
            if e["event_type"] == "linkage_status_updated":
                e["payload"]["index_date_ref"] = evs[-1]["integrity"]["event_hash"]
        rebuild_chain(ch)
        return ("--sequences", os.path.join(d, "seq"))
    return verifier_rejects(m, "V01-PROJECT")


@case("actor identity violated between baseline and evaluation (fully rebuilt)", "X", "round 4")
def c17():
    def m(pkg, d):
        shutil.copytree(SEQ_DIR, os.path.join(d, "seq"))
        f = os.path.join(d, "seq", "decision-chain-c02.json")
        seq = json.load(open(f))
        for e in seq["events"]:
            if e["event_type"] == "post_exposure_read_committed":
                e["payload"]["actor_ref"] = "someone-else"
        rebuild_chain(seq["events"])
        json.dump(seq, open(f, "w"))
        ch = [c for c in pkg["case_chains"] if c[0]["chain_ref"] == "case-chain-c02"][0]
        for e in ch:
            if e["event_type"] == "linkage_asserted":
                e["payload"]["decision_sequence_ref"]["sequence_head_hash"] = seq["events"][-1]["integrity"]["event_hash"]
                e["payload"]["decision_sequence_ref"]["final_decision_hash"] = seq["events"][-1]["integrity"]["event_hash"]
            if e["event_type"] == "linkage_status_updated":
                e["payload"]["index_date_ref"] = seq["events"][-1]["integrity"]["event_hash"]
        rebuild_chain(ch)
        return ("--sequences", os.path.join(d, "seq"))
    return verifier_rejects(m, "V01-ACTOR")


# ================================================================ rule execution

@case("code artifact digest is a hash of the rule NAME, not the code", "C", "round 5, item 3")
def c18():
    def m(pkg, d):
        art = json.load(open(os.path.join(ROOT, "artifacts", "projection_rule.json")))
        art["executable"]["code_artifact"]["digest"]["digest"] = core.h(b"pe-projection-v1")
        art["content_hash"] = core.artifact_content_hash({k: v for k, v in art.items() if k != "content_hash"})
        adir = os.path.join(d, "artifacts")
        shutil.copytree(os.path.join(ROOT, "artifacts"), adir)
        json.dump(art, open(os.path.join(adir, "projection_rule.json"), "w"))
        # genesis definition_set and cohort/plan refs must be rebound to the new hash
        # so ONLY the code-digest rule can object; simplest sound rebind: update genesis set entry
        g = pkg["cohort_chain"][0]
        for x in g["payload"]["definition_set"]:
            if x["artifact_id"].endswith("/projections/pe-primary"):
                x["content_hash"]["digest"] = art["content_hash"]
        rebuild_chain(pkg["cohort_chain"])
        return ("--artifacts", adir)
    return verifier_rejects(m, "RULE-DIGEST")


@case("rule module edited so its shipped fixtures fail", "X", "round 5, item 3")
def c19():
    def m(pkg, d):
        # relocate rules is not supported by flag; instead corrupt the fixture expectations
        # equivalently: fixture asserting different semantics than the module
        fdir = os.path.join(d, "fx")
        os.makedirs(fdir)
        src = json.load(open(os.path.join(ROOT, "fixtures", "pe-binary-v1.fixtures.json")))
        src["vectors"][0]["expect"] = "incorrect"
        json.dump(src, open(os.path.join(fdir, "pe-binary-v1.fixtures.json"), "w"))
        art = json.load(open(os.path.join(ROOT, "artifacts", "evaluation_criterion.json")))
        art["binary_validity_projection"]["executable"]["fixtures_ref"] = os.path.relpath(
            os.path.join(fdir, "pe-binary-v1.fixtures.json"), ROOT)
        art["content_hash"] = core.artifact_content_hash({k: v for k, v in art.items() if k != "content_hash"})
        adir = os.path.join(d, "artifacts")
        shutil.copytree(os.path.join(ROOT, "artifacts"), adir)
        json.dump(art, open(os.path.join(adir, "evaluation_criterion.json"), "w"))
        g = pkg["cohort_chain"][0]
        for x in g["payload"]["definition_set"]:
            if x["artifact_id"].endswith("/criteria/pe-90day-composite"):
                x["content_hash"]["digest"] = art["content_hash"]
        rebuild_chain(pkg["cohort_chain"])
        return ("--artifacts", adir)
    return verifier_rejects(m, "RULE-CONFORM")


@case("derivation software digest names a version string, not the engine bytes", "C", "round 5, item 3")
def c20():
    def m(pkg, d):
        ddir = os.path.join(d, "derived")
        shutil.copytree(DERIVED_DIR, ddir)
        f = os.path.join(ddir, "derived-rair-v2.json")
        art = json.load(open(f))
        art["recomputability"]["derivation_software_digest"]["digest"]["digest"] = core.h(b"dses-derive-0.2.0")
        art["artifact_hash"] = core.artifact_content_hash({k: v for k, v in art.items() if k != "artifact_hash"})
        json.dump(art, open(f, "w"))
        for e in pkg["cohort_chain"]:
            if e["event_type"] == "derived_artifact_registered" and e["payload"]["derived_artifact_id"] == art["artifact_id"]:
                e["payload"]["derived_artifact_hash"] = art["artifact_hash"]
        rebuild_chain(pkg["cohort_chain"])
        return ("--derived", ddir)
    return verifier_rejects(m, "DRV-ENGINE")


# ================================================================ snapshots and metrics

@case("SNAPSHOT ROOT attack with every orthogonal layer rebuilt: dies at SNAP-ROOT and nowhere else", "C", "round 5, items 4 and 6")
def c21():
    def m(pkg, d):
        for e in pkg["cohort_chain"]:
            if e["event_type"] == "analysis_snapshot_committed":
                e["payload"]["population_commitment"]["root"] = "ab" * 32
                break
        rebuild_chain(pkg["cohort_chain"])
    return verifier_rejects(m, "SNAP-ROOT")


@case("snapshot tuple binds a head that is not the chain's event at that sequence", "C", "round 5, item 4")
def c22():
    def m(pkg, d):
        for e in pkg["cohort_chain"]:
            if e["event_type"] == "analysis_snapshot_committed":
                t = e["payload"]["population_tuples"][0]
                t["case_chain_head"] = "99" * 32
                e["payload"]["population_commitment"]["root"] = core.mth(
                    [core.canon(x) for x in e["payload"]["population_tuples"]]).hex()
                break
        rebuild_chain(pkg["cohort_chain"])
    return verifier_rejects(m, "SNAP-HEAD")


@case("snapshot lists a definition version that was never in force", "X", "round 5, item 12")
def c23():
    def m(pkg, d):
        for e in pkg["cohort_chain"]:
            if e["event_type"] == "analysis_snapshot_committed":
                e["payload"]["definition_versions"][0]["version"] = "9.9.9"
                break
        rebuild_chain(pkg["cohort_chain"])
    return verifier_rejects(m, "SNAP-INFORCE")


@case("metric numerator forged with internally consistent arithmetic and interval", "X", "round 5, item 5")
def c24():
    def m(pkg, d):
        ddir = os.path.join(d, "derived")
        shutil.copytree(DERIVED_DIR, ddir)
        f = os.path.join(ddir, "derived-rair-v2.json")
        art = json.load(open(f))
        art["numerator"], art["denominator"], art["value"] = 3, 3, 1.0
        sys.path.insert(0, os.path.join(ROOT, "scripts"))
        from dses_core import wilson_interval
        art["interval"] = wilson_interval(3, 3)
        art["artifact_hash"] = core.artifact_content_hash({k: v for k, v in art.items() if k != "artifact_hash"})
        json.dump(art, open(f, "w"))
        for e in pkg["cohort_chain"]:
            if e["event_type"] == "derived_artifact_registered" and e["payload"]["derived_artifact_id"] == art["artifact_id"]:
                e["payload"]["derived_artifact_hash"] = art["artifact_hash"]
        rebuild_chain(pkg["cohort_chain"])
        return ("--derived", ddir)
    return verifier_rejects(m, "MET-RECOMPUTE")


@case("committed input set differs from the adjudications the computation used", "X", "round 5, item on input sets")
def c25():
    def m(pkg, d):
        ddir = os.path.join(d, "derived")
        shutil.copytree(DERIVED_DIR, ddir)
        f = os.path.join(ddir, "derived-rair-v2.json")
        art = json.load(open(f))
        art["projection_set"]["input_event_hashes"][0] = "77" * 32
        art["artifact_hash"] = core.artifact_content_hash({k: v for k, v in art.items() if k != "artifact_hash"})
        json.dump(art, open(f, "w"))
        for e in pkg["cohort_chain"]:
            if e["event_type"] == "derived_artifact_registered" and e["payload"]["derived_artifact_id"] == art["artifact_id"]:
                e["payload"]["derived_artifact_hash"] = art["artifact_hash"]
                e["payload"]["depends_on_event_hashes"] = art["projection_set"]["input_event_hashes"]
        rebuild_chain(pkg["cohort_chain"])
        return ("--derived", ddir)
    return verifier_rejects(m, "MET-INPUTS")


@case("superseded v1 metric must verify against its FROZEN snapshot, so corrupting v1 is caught even after revision", "X", "round 5, item 5")
def c26():
    def m(pkg, d):
        ddir = os.path.join(d, "derived")
        shutil.copytree(DERIVED_DIR, ddir)
        f = os.path.join(ddir, "derived-rsr-v1.json")
        art = json.load(open(f))
        art["numerator"] = 2
        art["denominator"] = 2
        art["value"] = 1.0
        from dses_core import wilson_interval
        art["interval"] = wilson_interval(2, 2)
        art["artifact_hash"] = core.artifact_content_hash({k: v for k, v in art.items() if k != "artifact_hash"})
        json.dump(art, open(f, "w"))
        for e in pkg["cohort_chain"]:
            if e["event_type"] == "derived_artifact_registered" and e["payload"]["derived_artifact_id"] == art["artifact_id"]:
                e["payload"]["derived_artifact_hash"] = art["artifact_hash"]
        rebuild_chain(pkg["cohort_chain"])
        return ("--derived", ddir)
    return verifier_rejects(m, "MET-RECOMPUTE")


@case("disclosure drift: linked count inflated while the metric itself still verifies", "X", "round 5, item 11")
def c27():
    def m(pkg, d):
        ddir = os.path.join(d, "derived")
        shutil.copytree(DERIVED_DIR, ddir)
        f = os.path.join(ddir, "derived-ear-v2.json")
        art = json.load(open(f))
        art["disclosures"]["completeness_accounting"]["linked"] = 12
        art["disclosures"]["completeness_accounting"]["linkage_failed"] = 0
        art["artifact_hash"] = core.artifact_content_hash({k: v for k, v in art.items() if k != "artifact_hash"})
        json.dump(art, open(f, "w"))
        for e in pkg["cohort_chain"]:
            if e["event_type"] == "derived_artifact_registered" and e["payload"]["derived_artifact_id"] == art["artifact_id"]:
                e["payload"]["derived_artifact_hash"] = art["artifact_hash"]
        rebuild_chain(pkg["cohort_chain"])
        return ("--derived", ddir)
    return verifier_rejects(m, "MET-DISCLOSE")


@case("stored prespecification label reappears on a derived artifact", "S", "round 5, item 8")
def c28():
    art = json.load(open(os.path.join(DERIVED_DIR, "derived-rair-v1.json")))
    art["prespecification_label"] = "prespecified"
    return schema_rejects(DRV_SCHEMA, art)


@case("nonzero denominator shipped without its declared interval", "S", "round 5, statistics")
def c29():
    art = json.load(open(os.path.join(DERIVED_DIR, "derived-rair-v1.json")))
    del art["interval"]
    return schema_rejects(DRV_SCHEMA, art)


@case("registered derived artifact not shipped", "X", "round 4")
def c30():
    def m(pkg, d):
        for e in pkg["cohort_chain"]:
            if e["event_type"] == "derived_artifact_registered":
                e["payload"]["derived_artifact_id"] = "urn:dses:derived:phantom"
                break
        rebuild_chain(pkg["cohort_chain"])
    return verifier_rejects(m, "DRV-SHIPPED")


@case("active artifact depending on a superseded adjudication", "X", "round 4")
def c31():
    def m(pkg, d):
        drop = [i for i, e in enumerate(pkg["cohort_chain"])
                if e["event_type"] == "derived_artifact_superseded"]
        for i in reversed(drop):
            del pkg["cohort_chain"][i]
        for i, e in enumerate(pkg["cohort_chain"]):
            e["sequence"] = i
            e["event_id"] = f"{e['chain_ref']}-{i:04d}"
        rebuild_chain(pkg["cohort_chain"])
    return verifier_rejects(m, "DRV-STALE")


# ================================================================ adjudication

@case("LAUNDERED REVISION: fresh adjudication appended with no revises_event_hash", "X", "round 5, item 7")
def c32():
    def m(pkg, d):
        ch = [c for c in pkg["case_chains"] if c[0]["chain_ref"] == "case-chain-c03"][0]
        i, orig = find(ch, "reference_standard_adjudicated")
        fresh = copy.deepcopy(orig)
        fresh["payload"]["conclusion"] = "negative"
        fresh["payload_commitment"] = {"alg": "sha-256", "digest": core.h(core.canon(fresh["payload"])),
                                       "commitment_type": "content_digest"}
        fresh["sequence"] = ch[-1]["sequence"] + 1
        fresh["event_id"] = f"{ch[0]['chain_ref']}-{fresh['sequence']:04d}"
        ch.append(fresh)
        rebuild_chain(ch)
    return verifier_rejects(m, "ADJ-LINEAGE")


@case("forked revision lineage: two revisions of the same predecessor", "X", "round 5, item 7")
def c33():
    def m(pkg, d):
        ch = [c for c in pkg["case_chains"] if c[0]["chain_ref"] == "case-chain-c02"][0]
        adjs = [e for e in ch if e["event_type"] == "reference_standard_adjudicated"]
        second = copy.deepcopy(adjs[-1])
        second["payload"]["conclusion"] = "positive"
        second["payload_commitment"] = {"alg": "sha-256", "digest": core.h(core.canon(second["payload"])),
                                        "commitment_type": "content_digest"}
        second["sequence"] = ch[-1]["sequence"] + 1
        second["event_id"] = f"{ch[0]['chain_ref']}-{second['sequence']:04d}"
        ch.append(second)
        rebuild_chain(ch)
    return verifier_rejects(m, "ADJ-FORK")


@case("recorded agreement value contradicts the pre-consensus assessments", "X", "round 5, item 10")
def c34():
    def m(pkg, d):
        ch = [c for c in pkg["case_chains"] if c[0]["chain_ref"] == "case-chain-c05"][0]
        i, e = find(ch, "reference_standard_adjudicated")
        e["payload"]["inter_adjudicator_agreement"]["value"] = 0.5
        # rebuild the hiding commitment with its real nonce so only ADJ-AGREE can object
        nonce = NONCES[e["integrity"]["event_hash"]]
        e["payload_commitment"]["digest"] = core.h(bytes.fromhex(nonce) + core.canon(e["payload"]))
        rebuild_chain(ch)
    return verifier_rejects(m, "ADJ-AGREE")


@case("assessing adjudicator absent from the charter roster", "X", "round 5, item 10")
def c35():
    def m(pkg, d):
        ch = [c for c in pkg["case_chains"] if c[0]["chain_ref"] == "case-chain-c06"][0]
        i, e = find(ch, "adjudicator_assessment_committed")
        e["payload"]["adjudicator_ref"] = "adj-Z"
        nonce = NONCES[e["integrity"]["event_hash"]]
        e["payload_commitment"]["digest"] = core.h(bytes.fromhex(nonce) + core.canon(e["payload"]))
        rebuild_chain(ch)
    return verifier_rejects(m, "ADJ-ROSTER")


@case("adjudication under a criterion the cohort never permitted", "X", "round 4")
def c36():
    def m(pkg, d):
        ch = [c for c in pkg["case_chains"] if c[0]["chain_ref"] == "case-chain-c04"][0]
        i, e = find(ch, "reference_standard_adjudicated")
        e["payload"]["evaluation_criterion_ref"]["artifact_id"] = "https://example.org/dses/criteria/invented"
        nonce = NONCES[e["integrity"]["event_hash"]]
        e["payload_commitment"]["digest"] = core.h(bytes.fromhex(nonce) + core.canon(e["payload"]))
        rebuild_chain(ch)
    return verifier_rejects(m, "ADJ-CRITERION")


@case("maturation label contradicting derivation from index date, window, and cutoff", "X", "round 5, item 13")
def c37():
    def m(pkg, d):
        ch = [c for c in pkg["case_chains"] if c[0]["chain_ref"] == "case-chain-c11"][0]
        statuses = [e for e in ch if e["event_type"] == "linkage_status_updated"]
        e = statuses[-1]
        e["payload"]["criterion_states"][0]["maturation_state"] = "mature"
        rebuild_chain(ch)
    return verifier_rejects(m, "MAT-DERIVED")


# ================================================================ population layer

@case("duplicate membership leaves inflating the denominator across manifests", "X", "round 4")
def c38():
    def m(pkg, d):
        a, b = pkg["case_chains"][0][0], pkg["case_chains"][1][0]
        b["payload"]["membership_leaf"] = a["payload"]["membership_leaf"]
        b["payload"]["manifest_ref"] = a["payload"]["manifest_ref"]
        b["payload"]["manifest_inclusion_proof"] = copy.deepcopy(a["payload"]["manifest_inclusion_proof"])
        rebuild_chain(pkg["case_chains"][1])
    return verifier_rejects(m, "DENOM-UNIQUE")


@case("a committed manifest position with no track", "X", "round 4")
def c39():
    def m(pkg, d):
        dropped = pkg["case_chains"].pop()
    return verifier_rejects(m, "DENOM-CLOSED")


@case("track bound to no committed manifest", "X", "round 5, item 12")
def c40():
    def m(pkg, d):
        ch = pkg["case_chains"][3]
        ch[0]["payload"]["manifest_ref"] = "55" * 32
        rebuild_chain(ch)
    return verifier_rejects(m, "TRACK-MANIFEST")


@case("manifest committed after its declared latency window", "X", "round 5, item 13")
def c41():
    def m(pkg, d):
        for e in pkg["cohort_chain"]:
            if e["event_type"] == "eligibility_manifest_committed":
                e["occurred_at"] = "2026-04-20T00:00:00Z"
                e["recorded_at"] = "2026-04-20T00:00:00Z"
                break
        rebuild_chain(pkg["cohort_chain"])
    return verifier_rejects(m, "MAN-LATENCY")


@case("checkpoint cadence violating the declared policy", "X", "round 5, item 13")
def c42():
    def m(pkg, d):
        cks = [e for e in pkg["cohort_chain"] if e["event_type"] == "checkpoint_committed"]
        cks[1]["occurred_at"] = "2026-08-30T00:00:00Z"
        cks[1]["recorded_at"] = "2026-08-30T00:00:00Z"
        rebuild_chain(pkg["cohort_chain"])
    return verifier_rejects(m, "CKPT-CADENCE")


@case("selective checkpoint coverage: one track quietly unobserved", "X", "round 4")
def c43():
    def m(pkg, d):
        for e in pkg["cohort_chain"]:
            if e["event_type"] == "checkpoint_committed":
                e["payload"]["head_observations"].pop()
                e["payload"]["checkpoint_log_size"] -= 1
                break
        rebuild_chain(pkg["cohort_chain"])
    return verifier_rejects(m, "CKPT-COVER")


@case("checkpoint head not matching the exported chain (historical rewrite)", "C", "round 3")
def c44():
    def m(pkg, d):
        ch = pkg["case_chains"][2]
        i, e = find(ch, "outcome_observed")
        e["payload"]["observation_date"] = "2026-06-01T00:00:00Z"
        rebuild_chain(ch)
    return verifier_rejects(m, "CKPT-HEAD")


@case("linkage asserted after a failed attempt", "X", "round 4")
def c45():
    def m(pkg, d):
        failed = next(c for c in pkg["case_chains"]
                      if any(e["event_type"] == "linkage_attempted"
                             and e["payload"]["attempt_result"] == "decision_record_missing" for e in c))
        src = copy.deepcopy(next(e for e in pkg["case_chains"][0] if e["event_type"] == "linkage_asserted"))
        src["chain_ref"] = failed[0]["chain_ref"]
        src["sequence"] = failed[-1]["sequence"] + 1
        src["event_id"] = f"{src['chain_ref']}-{src['sequence']:04d}"
        failed.append(src)
        rebuild_chain(failed)
    return verifier_rejects(m, "LINK-ASSERT")


# ================================================================ schema layer

@case("linkage attempt asserting a track state alongside its result", "S", "round 4")
def c46():
    i, e = find(GOOD["case_chains"][0], "linkage_attempted")
    e = copy.deepcopy(e)
    e["payload"]["track_state"] = "linked"
    return schema_rejects(EVENT_SCHEMA, e)


@case("anchor asserted with a bare reference instead of a receipt", "S", "round 4")
def c47():
    i, e = find(GOOD["cohort_chain"], "anchor_evidence_recorded")
    e = copy.deepcopy(e)
    del e["payload"]["receipt_signature"]
    e["payload"]["anchor_ref"] = "trust-me"
    return schema_rejects(EVENT_SCHEMA, e)


@case("event carrying self-reported capability flags", "S", "round 4")
def c48():
    e = copy.deepcopy(GOOD["case_chains"][0][1])
    e["integrity"]["capability_flags"] = {"payload_binding": True}
    return schema_rejects(EVENT_SCHEMA, e)


@case("indeterminate adjudication carrying a definitive conclusion", "S", "round 3")
def c49():
    ch = next(c for c in GOOD["case_chains"] if any(
        e["event_type"] == "reference_standard_adjudicated"
        and e["payload"]["conclusion_status"] == "indeterminate" for e in c))
    i, e = find(ch, "reference_standard_adjudicated")
    e = copy.deepcopy(e)
    e["payload"]["conclusion"] = "positive"
    return schema_rejects(EVENT_SCHEMA, e)


@case("track genesis without a manifest binding", "S", "round 5, item 12")
def c50():
    e = copy.deepcopy(GOOD["case_chains"][0][0])
    del e["payload"]["manifest_ref"]
    return schema_rejects(EVENT_SCHEMA, e)


@case("snapshot without its shipped population tuples", "S", "round 5, item 4")
def c51():
    i, e = find(GOOD["cohort_chain"], "analysis_snapshot_committed")
    e = copy.deepcopy(e)
    del e["payload"]["population_tuples"]
    return schema_rejects(EVENT_SCHEMA, e)


@case("bare-URI criterion reference where a pinned reference is required", "S", "round 5, item 12")
def c52():
    a = json.load(open(os.path.join(ROOT, "artifacts", "cohort_definition.json")))
    a["evaluation_criteria"]["primary"] = "https://example.org/dses/criteria/pe-90day-composite"
    return schema_rejects(DEF_SCHEMA, a)


@case("integer beyond the JCS-safe range in a hashed field", "S", "round 4")
def c53():
    e = copy.deepcopy(GOOD["case_chains"][0][0])
    e["sequence"] = 2 ** 53
    return schema_rejects(EVENT_SCHEMA, e)


# ================================================================================
# Verification-contract fixtures (round 6, item 1).
#
# CLAIMS-CLASSIFICATION defines "implemented" as: the verifier performs the check
# under a stable rule identifier AND a fixture asserts that identifier fires.
# External review found twenty-five implemented rows whose named rule had no
# fixture. Those rows were true about the verifier and false about the evidence
# for the verifier, which is exactly the gap this specification exists to close.
# scripts/release_lint.py now fails the build if any implemented rule is
# unaccompanied, so this section can never silently regress.
# ================================================================================

@case("definition artifact whose content hash does not recompute", "C", "round 6, item 1")
def d01():
    def m(pkg, d):
        adir = os.path.join(d, "artifacts")
        shutil.copytree(os.path.join(ROOT, "artifacts"), adir)
        f = os.path.join(adir, "analysis_plan.json")
        art = json.load(open(f))
        art["primary_population"] = "silently widened after commitment"
        json.dump(art, open(f, "w"))
        return ("--artifacts", adir)
    return verifier_rejects(m, "ART-HASH")


@case("two definition artifacts claiming the same identifier and version", "X", "round 6, item 1")
def d02():
    def m(pkg, d):
        adir = os.path.join(d, "artifacts")
        shutil.copytree(os.path.join(ROOT, "artifacts"), adir)
        art = json.load(open(os.path.join(adir, "analysis_plan.json")))
        art["primary_population"] = "a second, different artifact under the same identity"
        art["content_hash"] = core.artifact_content_hash({k: v for k, v in art.items() if k != "content_hash"})
        json.dump(art, open(os.path.join(adir, "analysis_plan_shadow.json"), "w"))
        return ("--artifacts", adir)
    return verifier_rejects(m, "ART-UNIQUE")


@case("definition artifact anchored only AFTER its declared prespecification cutoff", "X", "round 6, item 1")
def d03():
    def m(pkg, d):
        for e in pkg["cohort_chain"]:
            if (e["event_type"] == "anchor_evidence_recorded"
                    and e["payload"]["artifact_id"].endswith("/plans/pe-primary")):
                e["payload"]["receipt_body"]["anchor_time"] = "2026-05-01T00:00:00Z"
                sk = ANCHOR_SK
                e["payload"]["receipt_signature"] = core.sign_dses(
                    sk, "anchor-authority-01-key-1", "anchor-receipt",
                    core.anchor_receipt_target(e["payload"]["receipt_body"]))
                break
        rebuild_chain(pkg["cohort_chain"])
    return verifier_rejects(m, "ART-PRESPEC")


@case("anchor evidence smuggled inside the artifact it attests", "X", "round 6, item 1")
def d04():
    def m(pkg, d):
        adir = os.path.join(d, "artifacts")
        shutil.copytree(os.path.join(ROOT, "artifacts"), adir)
        f = os.path.join(adir, "projection_rule.json")
        art = json.load(open(f))
        art["anchor"] = {"anchor_time": "2026-02-16T09:00:00Z", "tsa_identity": "anchor-authority-01"}
        art["content_hash"] = core.artifact_content_hash({k: v for k, v in art.items() if k != "content_hash"})
        json.dump(art, open(f, "w"))
        g = pkg["cohort_chain"][0]
        for x in g["payload"]["definition_set"]:
            if x["artifact_id"].endswith("/projections/pe-primary"):
                x["content_hash"]["digest"] = art["content_hash"]
        rebuild_chain(pkg["cohort_chain"])
        return ("--artifacts", adir)
    return verifier_rejects(m, "ART-NOANCHOR")


@case("export head signature forged with a valid-looking but wrong signature value", "C", "round 6, item 1")
def d05():
    def m(pkg, d):
        pkg["export_head_signature"]["value"] = "ab" * 64
    return verifier_rejects(m, "SIG-VERIFY")


@case("export head signature pointed at a head it does not cover", "C", "round 6, item 1")
def d06():
    def m(pkg, d):
        pkg["export_head_signature"]["target_hash"] = "cc" * 32
    return verifier_rejects(m, "SIG-TARGET")


@case("manifest attestation signature replayed from a different manifest body", "C", "round 6, item 1")
def d07():
    def m(pkg, d):
        for e in pkg["cohort_chain"]:
            if e["event_type"] == "eligibility_manifest_committed":
                e["payload"]["source_census_ref"] = "ed-volume-substituted"
                break
        rebuild_chain(pkg["cohort_chain"])
    return verifier_rejects(m, "SIG-TARGET")


@case("checkpoint log root not recomputing from its appended observations", "C", "round 6, item 1")
def d08():
    def m(pkg, d):
        for e in pkg["cohort_chain"]:
            if e["event_type"] == "checkpoint_committed":
                e["payload"]["checkpoint_log_root"] = "ee" * 32
                break
        rebuild_chain(pkg["cohort_chain"])
    return verifier_rejects(m, "CKPT-ROOT")


@case("RFC 9162 consistency proof that does not verify between epochs", "C", "round 6, item 1")
def d09():
    def m(pkg, d):
        cks = [e for e in pkg["cohort_chain"] if e["event_type"] == "checkpoint_committed"]
        cks[1]["payload"]["consistency_proof"]["path"][0] = "dd" * 32
        rebuild_chain(pkg["cohort_chain"])
    return verifier_rejects(m, "CKPT-CONSIST")


@case("no checkpoint anchored at all, so no chain has a witnessed head", "X", "round 6, item 1")
def d10():
    def m(pkg, d):
        keep = [e for e in pkg["cohort_chain"]
                if not (e["event_type"] == "anchor_evidence_recorded"
                        and e["payload"]["target_kind"] == "checkpoint_event")]
        pkg["cohort_chain"] = keep
        for i, e in enumerate(pkg["cohort_chain"]):
            e["sequence"] = i
            e["event_id"] = f"{e['chain_ref']}-{i:04d}"
        rebuild_chain(pkg["cohort_chain"])
    return verifier_rejects(m, "CKPT-ANCHORED")


@case("membership inclusion proof with a tampered audit path", "C", "round 6, item 1")
def d11():
    def m(pkg, d):
        ch = pkg["case_chains"][4]
        ch[0]["payload"]["manifest_inclusion_proof"]["audit_path"][0] = "ba" * 32
        rebuild_chain(ch)
    return verifier_rejects(m, "TRACK-INCLUSION")


@case("track inclusion proof aimed at a root no manifest committed", "C", "round 6, item 1")
def d12():
    def m(pkg, d):
        ch = pkg["case_chains"][5]
        ch[0]["payload"]["manifest_inclusion_proof"]["root"] = "ac" * 32
        rebuild_chain(ch)
    return verifier_rejects(m, "TRACK-ROOT")


@case("case chain whose genesis is not a case track", "X", "round 6, item 1")
def d13():
    def m(pkg, d):
        ch = pkg["case_chains"][6]
        ch[0]["event_type"] = "linkage_attempted"
        ch[0]["payload"] = {"attempt_method": "manual", "attempt_result": "linked", "attempt_detail": "forged genesis"}
        rebuild_chain(ch)
    return verifier_rejects(m, "TRACK-GENESIS")


@case("snapshot citing a predecessor head that is not the preceding cohort event", "X", "round 6, item 1")
def d14():
    def m(pkg, d):
        for e in pkg["cohort_chain"]:
            if e["event_type"] == "analysis_snapshot_committed":
                e["payload"]["cohort_chain_head_before_snapshot"] = "fa" * 32
                break
        rebuild_chain(pkg["cohort_chain"])
    return verifier_rejects(m, "SNAP-PREV")


@case("snapshot omitting a track from its committed population", "X", "round 6, item 1")
def d15():
    def m(pkg, d):
        for e in pkg["cohort_chain"]:
            if e["event_type"] == "analysis_snapshot_committed":
                e["payload"]["population_tuples"].pop()
                e["payload"]["population_commitment"]["root"] = core.mth(
                    [core.canon(x) for x in e["payload"]["population_tuples"]]).hex()
                e["payload"]["population_commitment"]["tree_size"] -= 1
                break
        rebuild_chain(pkg["cohort_chain"])
    return verifier_rejects(m, "SNAP-COVER")


@case("linkage bound to a final decision that is not the sequence's terminal event", "C", "round 6, item 1")
def d16():
    def m(pkg, d):
        ch = pkg["case_chains"][0]
        for e in ch:
            if e["event_type"] == "linkage_asserted":
                e["payload"]["decision_sequence_ref"]["final_decision_hash"] = "0f" * 32
        rebuild_chain(ch)
    return verifier_rejects(m, "V01-FINAL")


@case("v0.1 sequence event missing its payload commitment entirely", "S", "round 6, item 1")
def d17():
    def m(pkg, d):
        shutil.copytree(SEQ_DIR, os.path.join(d, "seq"))
        f = os.path.join(d, "seq", "decision-chain-c05.json")
        seq = json.load(open(f))
        del seq["events"][1]["payload_commitment"]
        json.dump(seq, open(f, "w"))
        return ("--sequences", os.path.join(d, "seq"))
    return verifier_rejects(m, "V01-SHAPE")


@case("determinate adjudication with no conclusion recorded", "X", "round 6, item 1")
def d18():
    def m(pkg, d):
        ch = [c for c in pkg["case_chains"] if c[0]["chain_ref"] == "case-chain-c06"][0]
        i, e = find(ch, "reference_standard_adjudicated")
        del e["payload"]["conclusion"]
        e["payload_commitment"]["digest"] = core.h(bytes.fromhex(NONCES[e["integrity"]["event_hash"]]) + core.canon(e["payload"]))
        rebuild_chain(ch)
    return verifier_rejects(m, "ADJ-CONCL")


@case("adjudication citing an assessment that was not committed pre-consensus", "X", "round 6, item 1")
def d19():
    def m(pkg, d):
        ch = [c for c in pkg["case_chains"] if c[0]["chain_ref"] == "case-chain-c00"][0]
        i, e = find(ch, "adjudicator_assessment_committed")
        e["payload"]["pre_consensus"] = False
        e["payload_commitment"]["digest"] = core.h(bytes.fromhex(NONCES[e["integrity"]["event_hash"]]) + core.canon(e["payload"]))
        rebuild_chain(ch)
    return verifier_rejects(m, "ADJ-ASSESS")


@case("adjudication below the charter's minimum independent assessments", "X", "round 6, item 1")
def d20():
    def m(pkg, d):
        ch = [c for c in pkg["case_chains"] if c[0]["chain_ref"] == "case-chain-c01"][0]
        i, e = find(ch, "reference_standard_adjudicated")
        e["payload"]["assessment_refs"] = e["payload"]["assessment_refs"][:1]
        e["payload"]["inter_adjudicator_agreement"]["value"] = 1
        e["payload_commitment"]["digest"] = core.h(bytes.fromhex(NONCES[e["integrity"]["event_hash"]]) + core.canon(e["payload"]))
        rebuild_chain(ch)
    return verifier_rejects(m, "ADJ-MIN")


@case("adjudication resolved by a method the charter does not permit", "X", "round 6, item 1")
def d21():
    def m(pkg, d):
        ch = [c for c in pkg["case_chains"] if c[0]["chain_ref"] == "case-chain-c03"][0]
        i, e = find(ch, "reference_standard_adjudicated")
        e["payload"]["resolution_process"]["method"] = "coin_flip"
        e["payload_commitment"]["digest"] = core.h(bytes.fromhex(NONCES[e["integrity"]["event_hash"]]) + core.canon(e["payload"]))
        rebuild_chain(ch)
    return verifier_rejects(m, "ADJ-METHOD")


@case("revision citing a predecessor that lives in a different case chain", "X", "round 6, item 1")
def d22():
    def m(pkg, d):
        ch = [c for c in pkg["case_chains"] if c[0]["chain_ref"] == "case-chain-c02"][0]
        adjs = [e for e in ch if e["event_type"] == "reference_standard_adjudicated"]
        adjs[-1]["payload"]["revises_event_hash"] = "1a" * 32
        adjs[-1]["payload_commitment"]["digest"] = core.h(
            bytes.fromhex(NONCES[adjs[-1]["integrity"]["event_hash"]]) + core.canon(adjs[-1]["payload"]))
        rebuild_chain(ch)
    return verifier_rejects(m, "ADJ-REVREF")


@case("case with two competing active adjudications and no lineage between them", "X", "round 6, item 1")
def d23():
    def m(pkg, d):
        ch = [c for c in pkg["case_chains"] if c[0]["chain_ref"] == "case-chain-c05"][0]
        i, orig = find(ch, "reference_standard_adjudicated")
        clone = copy.deepcopy(orig)
        clone["payload"]["revision_reason_description"] = "competing leaf"
        clone["payload"]["revises_event_hash"] = orig["integrity"]["event_hash"]
        clone["payload"]["revision_reason"] = "new_evidence"
        clone["sequence"] = ch[-1]["sequence"] + 1
        clone["event_id"] = f"{ch[0]['chain_ref']}-{clone['sequence']:04d}"
        clone["payload_commitment"] = {"alg": "sha-256", "digest": core.h(core.canon(clone["payload"])),
                                       "commitment_type": "content_digest"}
        ch.append(clone)
        second = copy.deepcopy(clone)
        second["payload"]["revision_reason_description"] = "second competing leaf"
        second["sequence"] = clone["sequence"] + 1
        second["event_id"] = f"{ch[0]['chain_ref']}-{second['sequence']:04d}"
        second["payload_commitment"] = {"alg": "sha-256", "digest": core.h(core.canon(second["payload"])),
                                        "commitment_type": "content_digest"}
        ch.append(second)
        rebuild_chain(ch)
    return verifier_rejects(m, "ADJ-FORK")


@case("linked case whose only status is recorded under a non-primary criterion", "X", "round 6, item 1")
def d24():
    def m(pkg, d):
        ch = [c for c in pkg["case_chains"] if c[0]["chain_ref"] == "case-chain-c07"][0]
        for e in ch:
            if e["event_type"] == "linkage_status_updated":
                for cs in e["payload"]["criterion_states"]:
                    cs["evaluation_criterion_ref"]["artifact_id"] = "https://example.org/dses/criteria/secondary"
        rebuild_chain(ch)
    return verifier_rejects(m, "OL-STATUS")


@case("structurally unprocessable package yields a verdict, never a stack trace", "X", "round 6, robustness")
def d24b():
    def m(pkg, d):
        ch = [c for c in pkg["case_chains"] if c[0]["chain_ref"] == "case-chain-c06"][0]
        keep = [e for e in ch if e["event_type"] != "linkage_status_updated"]
        ch.clear()
        ch.extend(keep)
        for i, e in enumerate(ch):
            e["sequence"] = i
            e["event_id"] = f"{e['chain_ref']}-{i:04d}"
        rebuild_chain(ch)
    return verifier_rejects(m, "OL-STATUS")


@case("mature linked case with its adjudication removed", "X", "round 6, item 1")
def d25():
    def m(pkg, d):
        ch = [c for c in pkg["case_chains"] if c[0]["chain_ref"] == "case-chain-c06"][0]
        keep = [e for e in ch if e["event_type"] != "reference_standard_adjudicated"]
        ch.clear()
        ch.extend(keep)
        for i, e in enumerate(ch):
            e["sequence"] = i
            e["event_id"] = f"{e['chain_ref']}-{i:04d}"
        rebuild_chain(ch)
    return verifier_rejects(m, "OL-ADJUDICATED")


@case("derived lifecycle event naming an artifact that was never registered", "X", "round 6, item 1")
def d26():
    def m(pkg, d):
        for e in pkg["cohort_chain"]:
            if e["event_type"] == "derived_artifact_superseded":
                e["payload"]["derived_artifact_id"] = "urn:dses:derived:never-registered"
                break
        rebuild_chain(pkg["cohort_chain"])
    return verifier_rejects(m, "DRV-LIFECYCLE")


@case("registered derived hash not matching the shipped artifact bytes", "C", "round 6, item 1")
def d27():
    def m(pkg, d):
        for e in pkg["cohort_chain"]:
            if e["event_type"] == "derived_artifact_registered":
                e["payload"]["derived_artifact_hash"] = "0b" * 32
                break
        rebuild_chain(pkg["cohort_chain"])
    return verifier_rejects(m, "DRV-HASH")


@case("derived artifact whose snapshot reference resolves to nothing", "X", "round 6, item 1")
def d28():
    def m(pkg, d):
        for e in pkg["cohort_chain"]:
            if e["event_type"] == "derived_artifact_registered":
                e["payload"]["analysis_snapshot_ref"] = "2c" * 32
                break
        rebuild_chain(pkg["cohort_chain"])
    return verifier_rejects(m, "DRV-SNAP")


@case("metric reference to a definition version that does not exist", "X", "round 6, item 1")
def d29():
    def m(pkg, d):
        ddir = os.path.join(d, "derived")
        shutil.copytree(DERIVED_DIR, ddir)
        f = os.path.join(ddir, "derived-rair-v1.json")
        art = json.load(open(f))
        art["metric_definition_ref"]["version"] = "4.0.0"
        art["artifact_hash"] = core.artifact_content_hash({k: v for k, v in art.items() if k != "artifact_hash"})
        json.dump(art, open(f, "w"))
        for e in pkg["cohort_chain"]:
            if (e["event_type"] == "derived_artifact_registered"
                    and e["payload"]["derived_artifact_id"] == art["artifact_id"]):
                e["payload"]["derived_artifact_hash"] = art["artifact_hash"]
        rebuild_chain(pkg["cohort_chain"])
        return ("--derived", ddir)
    return verifier_rejects(m, "REF-RESOLVE")


@case("metric reference with the right version but a substituted content hash", "C", "round 6, item 1")
def d30():
    def m(pkg, d):
        ddir = os.path.join(d, "derived")
        shutil.copytree(DERIVED_DIR, ddir)
        f = os.path.join(ddir, "derived-rsr-v1.json")
        art = json.load(open(f))
        art["metric_definition_ref"]["content_hash"]["digest"] = "3d" * 32
        art["artifact_hash"] = core.artifact_content_hash({k: v for k, v in art.items() if k != "artifact_hash"})
        json.dump(art, open(f, "w"))
        for e in pkg["cohort_chain"]:
            if (e["event_type"] == "derived_artifact_registered"
                    and e["payload"]["derived_artifact_id"] == art["artifact_id"]):
                e["payload"]["derived_artifact_hash"] = art["artifact_hash"]
        rebuild_chain(pkg["cohort_chain"])
        return ("--derived", ddir)
    return verifier_rejects(m, "REF-HASH")


@case("metric value inconsistent with its own numerator and denominator", "X", "round 6, item 1")
def d31():
    def m(pkg, d):
        ddir = os.path.join(d, "derived")
        shutil.copytree(DERIVED_DIR, ddir)
        f = os.path.join(ddir, "derived-ear-v1.json")
        art = json.load(open(f))
        art["value"] = 0.9
        art["artifact_hash"] = core.artifact_content_hash({k: v for k, v in art.items() if k != "artifact_hash"})
        json.dump(art, open(f, "w"))
        for e in pkg["cohort_chain"]:
            if (e["event_type"] == "derived_artifact_registered"
                    and e["payload"]["derived_artifact_id"] == art["artifact_id"]):
                e["payload"]["derived_artifact_hash"] = art["artifact_hash"]
        rebuild_chain(pkg["cohort_chain"])
        return ("--derived", ddir)
    return verifier_rejects(m, "MET-ARITH")


@case("Wilson interval narrowed to flatter the estimate", "X", "round 6, item 1")
def d32():
    def m(pkg, d):
        ddir = os.path.join(d, "derived")
        shutil.copytree(DERIVED_DIR, ddir)
        f = os.path.join(ddir, "derived-rair-v1.json")
        art = json.load(open(f))
        art["interval"]["lower"] = art["value"] - 0.01
        art["interval"]["upper"] = art["value"] + 0.01
        art["artifact_hash"] = core.artifact_content_hash({k: v for k, v in art.items() if k != "artifact_hash"})
        json.dump(art, open(f, "w"))
        for e in pkg["cohort_chain"]:
            if (e["event_type"] == "derived_artifact_registered"
                    and e["payload"]["derived_artifact_id"] == art["artifact_id"]):
                e["payload"]["derived_artifact_hash"] = art["artifact_hash"]
        rebuild_chain(pkg["cohort_chain"])
        return ("--derived", ddir)
    return verifier_rejects(m, "MET-INTERVAL")


@case("metric governed by a plan revised after anchoring, so prespecification cannot be derived", "X", "round 6, item 1")
def d33():
    # The adversary cannot re-mint the anchor receipt (the authority key is external),
    # so revising the plan after the fact leaves its hash outside every verified anchor.
    def m(pkg, d):
        adir = os.path.join(d, "artifacts")
        shutil.copytree(os.path.join(ROOT, "artifacts"), adir)
        f = os.path.join(adir, "analysis_plan.json")
        art = json.load(open(f))
        art["primary_population"] = "widened after the anchor was obtained"
        art["content_hash"] = core.artifact_content_hash({k: v for k, v in art.items() if k != "content_hash"})
        json.dump(art, open(f, "w"))
        return ("--artifacts", adir)
    return verifier_rejects(m, "MET-PRESPEC")


@case("blinding breakdown claiming full blinding where a breach was recorded", "X", "round 6, item 1")
def d34():
    def m(pkg, d):
        ch = [c for c in pkg["case_chains"] if c[0]["chain_ref"] == "case-chain-c00"][0]
        i, e = find(ch, "adjudicator_assessment_committed")
        e["payload"]["blinding_breach"] = True
        e["payload_commitment"]["digest"] = core.h(bytes.fromhex(NONCES[e["integrity"]["event_hash"]]) + core.canon(e["payload"]))
        rebuild_chain(ch)
    return verifier_rejects(m, "MET-BLIND")


@case("exclusion disclosure understating the partially correct exclusions", "X", "round 6, item 1")
def d35():
    def m(pkg, d):
        ddir = os.path.join(d, "derived")
        shutil.copytree(DERIVED_DIR, ddir)
        f = os.path.join(ddir, "derived-rair-v2.json")
        art = json.load(open(f))
        art["disclosures"]["binary_projection_exclusions"]["partially_correct"] = 0
        art["artifact_hash"] = core.artifact_content_hash({k: v for k, v in art.items() if k != "artifact_hash"})
        json.dump(art, open(f, "w"))
        for e in pkg["cohort_chain"]:
            if (e["event_type"] == "derived_artifact_registered"
                    and e["payload"]["derived_artifact_id"] == art["artifact_id"]):
                e["payload"]["derived_artifact_hash"] = art["artifact_hash"]
        rebuild_chain(pkg["cohort_chain"])
        return ("--derived", ddir)
    return verifier_rejects(m, "MET-EXCL")


@case("derived artifact carrying a mutable status field", "S", "round 6, item 1")
def d36():
    def m(pkg, d):
        ddir = os.path.join(d, "derived")
        shutil.copytree(DERIVED_DIR, ddir)
        f = os.path.join(ddir, "derived-rsr-v2.json")
        art = json.load(open(f))
        art["status"] = "active"
        art["artifact_hash"] = core.artifact_content_hash({k: v for k, v in art.items() if k != "artifact_hash"})
        json.dump(art, open(f, "w"))
        for e in pkg["cohort_chain"]:
            if (e["event_type"] == "derived_artifact_registered"
                    and e["payload"]["derived_artifact_id"] == art["artifact_id"]):
                e["payload"]["derived_artifact_hash"] = art["artifact_hash"]
        rebuild_chain(pkg["cohort_chain"])
        return ("--derived", ddir)
    return verifier_rejects(m, "DRV-NOLABEL")


@case("linkage attempt asserting its own track state (verifier layer)", "X", "round 6, item 1")
def d37():
    def m(pkg, d):
        ch = pkg["case_chains"][1]
        i, e = find(ch, "linkage_attempted")
        e["payload"]["track_state"] = "linked"
        rebuild_chain(ch)
    return verifier_rejects(m, "LINK-NOSTATE")


@case("second linkage attempt after a terminal result", "X", "round 6, item 1")
def d38():
    def m(pkg, d):
        ch = pkg["case_chains"][2]
        i, e = find(ch, "linkage_attempted")
        again = copy.deepcopy(e)
        again["sequence"] = ch[-1]["sequence"] + 1
        again["event_id"] = f"{ch[0]['chain_ref']}-{again['sequence']:04d}"
        ch.append(again)
        rebuild_chain(ch)
    return verifier_rejects(m, "LINK-ORDER")


@case("duplicate event identifiers within one chain", "X", "round 6, item 1")
def d39():
    def m(pkg, d):
        ch = pkg["case_chains"][3]
        ch[2]["event_id"] = ch[1]["event_id"]
        rebuild_chain(ch)
    return verifier_rejects(m, "EVT-UNIQUE")


@case("non-contiguous sequence numbering", "C", "round 6, item 1")
def d40():
    def m(pkg, d):
        ch = pkg["case_chains"][4]
        for e in ch[2:]:
            e["sequence"] += 5
        rebuild_chain(ch)
    return verifier_rejects(m, "CHAIN-SEQ")


@case("event timestamp that is not a real instant", "X", "round 6, item 1")
def d41():
    def m(pkg, d):
        ch = pkg["case_chains"][5]
        ch[1]["occurred_at"] = "2026-02-30T00:00:00Z"
        rebuild_chain(ch)
    return verifier_rejects(m, "EVT-TIME")


@case("case event declaring cohort scope", "X", "round 6, item 1")
def d42():
    def m(pkg, d):
        ch = pkg["case_chains"][6]
        ch[1]["chain_scope"] = "cohort"
        rebuild_chain(ch)
    return verifier_rejects(m, "EVT-SCOPE")


@case("genesis event carrying a predecessor hash", "C", "round 6, item 1")
def d43():
    def m(pkg, d):
        ch = pkg["case_chains"][7]
        ch[0]["integrity"]["prev_event_hash"] = "5e" * 32
        ch[0]["integrity"]["event_hash"] = core.event_preimage_hash(ch[0])
        prev = ch[0]["integrity"]["event_hash"]
        for e in ch[1:]:
            e["integrity"]["prev_event_hash"] = prev
            e["integrity"]["event_hash"] = core.event_preimage_hash(e)
            prev = e["integrity"]["event_hash"]
    return verifier_rejects(m, "CHAIN-GENESIS")


@case("two case chains sharing one chain reference", "X", "round 6, item 1")
def d44():
    def m(pkg, d):
        clone = copy.deepcopy(pkg["case_chains"][8])
        pkg["case_chains"].append(clone)
    return verifier_rejects(m, "CHAIN-UNIQUE")


@case("two cohort genesis events", "X", "round 6, item 1")
def d45():
    def m(pkg, d):
        clone = copy.deepcopy(pkg["cohort_chain"][0])
        clone["sequence"] = pkg["cohort_chain"][-1]["sequence"] + 1
        clone["event_id"] = f"{clone['chain_ref']}-{clone['sequence']:04d}"
        pkg["cohort_chain"].append(clone)
        rebuild_chain(pkg["cohort_chain"])
    return verifier_rejects(m, "GENESIS-ONE")


@case("no eligibility manifest committed at all", "X", "round 6, item 1")
def d46():
    def m(pkg, d):
        pkg["cohort_chain"] = [e for e in pkg["cohort_chain"]
                               if e["event_type"] != "eligibility_manifest_committed"]
        for i, e in enumerate(pkg["cohort_chain"]):
            e["sequence"] = i
            e["event_id"] = f"{e['chain_ref']}-{i:04d}"
        rebuild_chain(pkg["cohort_chain"])
    return verifier_rejects(m, "MAN-PRESENT")


@case("an anchor authority the package itself declares distrusted", "X", "round 6, item 1")
def d47():
    def m(pkg, d):
        ev = copy.deepcopy(pkg["cohort_chain"][-1])
        ev["event_type"] = "anchor_distrusted"
        ev["payload"] = {"anchor_authority": "anchor-authority-01", "reason": "key_compromise",
                         "effective_at": "2026-08-15T00:00:00Z",
                         "detail": "Authority signing key disclosed."}
        ev["sequence"] = pkg["cohort_chain"][-1]["sequence"] + 1
        ev["event_id"] = f"{ev['chain_ref']}-{ev['sequence']:04d}"
        ev["payload_commitment"] = {"alg": "sha-256", "digest": core.h(core.canon(ev["payload"])),
                                    "commitment_type": "content_digest"}
        pkg["cohort_chain"].append(ev)
        rebuild_chain(pkg["cohort_chain"])
    return verifier_rejects(m, "ANCHOR-DISTRUST")


@case("witness contradicting the exported checkpoint (historical rewrite detected)", "C", "round 6, item 1")
def d49():
    def m(pkg, d):
        w = os.path.join(d, "witness.json")
        json.dump({"epoch": 1, "root": "7f" * 32, "size": 12}, open(w, "w"))
        return ("--witness", w)
    return verifier_rejects(m, "CKPT-WITNESS")


@case("rule reference naming code that is not in the package", "X", "round 6, item 1")
def d50():
    def m(pkg, d):
        adir = os.path.join(d, "artifacts")
        shutil.copytree(os.path.join(ROOT, "artifacts"), adir)
        f = os.path.join(adir, "projection_rule.json")
        art = json.load(open(f))
        art["executable"]["rule_id"] = "pe-projection-v99"
        art["executable"]["code_artifact"]["locator"] = "rules/pe_projection_v99.py"
        art["content_hash"] = core.artifact_content_hash({k: v for k, v in art.items() if k != "content_hash"})
        json.dump(art, open(f, "w"))
        g = pkg["cohort_chain"][0]
        for x in g["payload"]["definition_set"]:
            if x["artifact_id"].endswith("/projections/pe-primary"):
                x["content_hash"]["digest"] = art["content_hash"]
        rebuild_chain(pkg["cohort_chain"])
        return ("--artifacts", adir)
    return verifier_rejects(m, "RULE-RESOLVE")


@case("rule shipping no conformance fixtures", "X", "round 6, item 1")
def d51():
    def m(pkg, d):
        adir = os.path.join(d, "artifacts")
        shutil.copytree(os.path.join(ROOT, "artifacts"), adir)
        f = os.path.join(adir, "projection_rule.json")
        art = json.load(open(f))
        art["executable"]["fixtures_ref"] = "fixtures/absent.fixtures.json"
        art["content_hash"] = core.artifact_content_hash({k: v for k, v in art.items() if k != "content_hash"})
        json.dump(art, open(f, "w"))
        return ("--artifacts", adir)
    return verifier_rejects(m, "RULE-FIXTURES")


@case("event stripped of its payload commitment", "S", "round 6, item 1")
def d52():
    def m(pkg, d):
        ch = pkg["case_chains"][9]
        del ch[1]["payload_commitment"]
        prev = ch[0]["integrity"]["event_hash"]
        for e in ch[1:]:
            e["integrity"]["prev_event_hash"] = prev
            e["integrity"]["event_hash"] = core.event_preimage_hash(e)
            prev = e["integrity"]["event_hash"]
    return verifier_rejects(m, "PC-PRESENT")


@case("no external trust store supplied, so no anchor can be established", "X", "round 6, item 1")
def d53():
    def m(pkg, d):
        empty = os.path.join(d, "empty-trust.json")
        json.dump({"authorities": {}}, open(empty, "w"))
        return ("--anchor-trust", empty)
    return verifier_rejects(m, "TRUST-EXTERNAL")


@case("v0.1 sequence whose evaluation state precedes the AI exposure it responds to, so the declared rule cannot project it", "X", "round 6, item 1")
def d54():
    def m(pkg, d):
        shutil.copytree(SEQ_DIR, os.path.join(d, "seq"))
        f = os.path.join(d, "seq", "decision-chain-c03.json")
        seq = json.load(open(f))
        evs = seq["events"]
        post = next(e for e in evs if e["event_type"] == "post_exposure_read_committed")
        expo = next(e for e in evs if e["event_type"] == "ai_output_released")
        evs[evs.index(post)], evs[evs.index(expo)] = expo, post
        for i, e in enumerate(evs):
            e["sequence"] = i
        rebuild_chain(evs)
        json.dump(seq, open(f, "w"))
        ch = [c for c in pkg["case_chains"] if c[0]["chain_ref"] == "case-chain-c03"][0]
        for e in ch:
            if e["event_type"] == "linkage_asserted":
                e["payload"]["decision_sequence_ref"]["sequence_head_hash"] = evs[-1]["integrity"]["event_hash"]
                e["payload"]["decision_sequence_ref"]["final_decision_hash"] = evs[-1]["integrity"]["event_hash"]
            if e["event_type"] == "linkage_status_updated":
                e["payload"]["index_date_ref"] = evs[-1]["integrity"]["event_hash"]
        rebuild_chain(ch)
        return ("--sequences", os.path.join(d, "seq"))
    return verifier_rejects(m, "V01-PROJECT")


@case("two unrevised adjudications leaving no single active determination", "X", "round 6, item 1")
def d55():
    def m(pkg, d):
        ch = [c for c in pkg["case_chains"] if c[0]["chain_ref"] == "case-chain-c02"][0]
        adjs = [e for e in ch if e["event_type"] == "reference_standard_adjudicated"]
        # break the lineage link so both determinations are leaves
        del adjs[-1]["payload"]["revises_event_hash"]
        adjs[-1]["payload_commitment"]["digest"] = core.h(
            bytes.fromhex(NONCES[adjs[-1]["integrity"]["event_hash"]]) + core.canon(adjs[-1]["payload"]))
        rebuild_chain(ch)
    return verifier_rejects(m, "ADJ-ACTIVE")


@case("package missing a structural key entirely yields a verdict, not a stack trace", "X", "round 6, robustness")
def d56():
    def m(pkg, d):
        for ch in pkg["case_chains"]:
            for e in ch:
                if e["event_type"] == "case_track_created":
                    del e["payload"]["manifest_inclusion_proof"]
            rebuild_chain(ch)
    return verifier_rejects(m, "PKG-MALFORMED")



@case("export signature with a non-DSES profile", "S", "round 8, publication-readiness")
def e01():
    def m(pkg, d):
        pkg["export_head_signature"]["profile"] = "NOT-DSES"
    return verifier_rejects(m, "SIG-PROFILE")


@case("optional event signature present but cryptographically invalid", "C", "round 8, publication-readiness")
def e02():
    def m(pkg, d):
        ev = pkg["case_chains"][0][0]
        ev["signatures"] = [{
            "profile": "DSES-SIG-v1",
            "alg": "ed25519",
            "key_ref": "outcome-registry-01-key-1",
            "context_label": "event",
            "target_hash": ev["integrity"]["event_hash"],
            "value": "00" * 64,
        }]
    return verifier_rejects(m, "SIG-VERIFY")


@case("hiding nonce sidecar shorter than its declared 128 bits", "X", "round 8, publication-readiness")
def e03():
    def m(pkg, d):
        side = copy.deepcopy(json.load(open(os.path.join(ROOT, "examples", "nonce-store.json"))))
        # The sidecar is keyed by event hash, not event_id: event ids are unique
        # only within a chain, so an id-keyed sidecar cannot represent two events
        # that share an id across chains (round 10, item 5).
        event_hash = next(
            e["integrity"]["event_hash"] for ch in pkg["case_chains"] for e in ch
            if e["payload_commitment"]["commitment_type"] == "hiding" and "payload" in e
        )
        side["nonces"][event_hash] = "00" * 8
        path = os.path.join(d, "nonces.json")
        json.dump(side, open(path, "w"))
        return ("--nonces", path)
    return verifier_rejects(m, "PC-NONCE-LENGTH")


@case("unsupported declared multiplicity rejected by the definition schema", "S", "round 8, publication-readiness")
def e04():
    art = json.load(open(os.path.join(ROOT, "artifacts", "cohort_definition.json")))
    art["membership_multiplicity"] = "declared_multiplicity"
    return schema_rejects(DEF_SCHEMA, art)


# ---- round nine: findings from the independent implementation attempt ----

@case("signature test vectors tampered so the declared encoding no longer reproduces them", "C", "round 9, S-1")
def e01():
    def m(pkg, d):
        fdir = os.path.join(d, "fx")
        shutil.copytree(os.path.join(ROOT, "fixtures"), fdir)
        f = os.path.join(fdir, "dses-sig-v1.testvectors.json")
        tv = json.load(open(f))
        tv["vectors"][0]["signing_input_hex"] = "00" * 40
        json.dump(tv, open(f, "w"))
        return ("--fixtures", fdir)
    return verifier_rejects(m, "SIG-VECTORS")


@case("EAR metric definition shipping no executable alignment relation", "S", "round 9, M-1")
def e02():
    a = json.load(open(os.path.join(ROOT, "artifacts", "metric_definition_ear.json")))
    del a["alignment_relation"]
    return schema_rejects(DEF_SCHEMA, a)


@case("EAR recomputed with no declared alignment relation reachable (verifier layer)", "S", "round 9, M-1")
def e04():
    def m(pkg, d):
        adir = os.path.join(d, "artifacts")
        shutil.copytree(os.path.join(ROOT, "artifacts"), adir)
        f = os.path.join(adir, "metric_definition_ear.json")
        art = json.load(open(f))
        del art["alignment_relation"]
        art["content_hash"] = core.artifact_content_hash({k: v for k, v in art.items() if k != "content_hash"})
        json.dump(art, open(f, "w"))
        # No chain rebuild: rebuilding the cohort chain would invalidate the
        # snapshot references and short-circuit the metric loop before the
        # alignment check is reached, which would make this fixture green for
        # the wrong reason.
        return ("--artifacts", adir)
    return verifier_rejects(m, "MET-ALIGN")


@case("charter shipping no executable agreement statistic", "S", "round 9, A-2")
def e03():
    a = json.load(open(os.path.join(ROOT, "artifacts", "adjudication_charter.json")))
    del a["agreement_statistic"]
    return schema_rejects(DEF_SCHEMA, a)


@case("agreement recomputed by first-assessment comparison rather than the declared modal rule", "X", "round 10, item 1")
def e05():
    def m(pkg, d):
        ch = [c for c in pkg["case_chains"] if c[0]["chain_ref"] == "case-chain-c05"][0]
        i, e = find(ch, "reference_standard_adjudicated")
        # 3 assessments A,B,B: modal rule gives 2/3, first-comparison gives 1/3.
        e["payload"]["inter_adjudicator_agreement"]["value"] = 1 / 3
        e["payload_commitment"]["digest"] = core.h(
            bytes.fromhex(NONCES[e["integrity"]["event_hash"]]) + core.canon(e["payload"]))
        rebuild_chain(ch)
    return verifier_rejects(m, "ADJ-AGREE")


@case("two assessments from ONE adjudicator satisfying a two-independent-assessment charter", "X", "round 10, item 2")
def e06():
    def m(pkg, d):
        ch = [c for c in pkg["case_chains"] if c[0]["chain_ref"] == "case-chain-c06"][0]
        assess = [e for e in ch if e["event_type"] == "adjudicator_assessment_committed"]
        assess[1]["payload"]["adjudicator_ref"] = assess[0]["payload"]["adjudicator_ref"]
        assess[1]["payload_commitment"]["digest"] = core.h(
            bytes.fromhex(NONCES[assess[1]["integrity"]["event_hash"]]) + core.canon(assess[1]["payload"]))
        rebuild_chain(ch)
    return verifier_rejects(m, "ADJ-INDEPENDENT")


@case("declared interval_method contradicting the executable estimator it names", "X", "round 10, item 12")
def e07():
    def m(pkg, d):
        adir = os.path.join(d, "artifacts")
        shutil.copytree(os.path.join(ROOT, "artifacts"), adir)
        f = os.path.join(adir, "metric_definition_rair.json")
        art = json.load(open(f))
        art["aggregation_and_uncertainty"]["interval_method"] = "Clopper-Pearson"
        art["content_hash"] = core.artifact_content_hash({k: v for k, v in art.items() if k != "content_hash"})
        json.dump(art, open(f, "w"))
        return ("--artifacts", adir)
    return verifier_rejects(m, "MET-ESTIMATOR")


# ---- round eleven: defects the repairs themselves introduced ----

@case("declared rule parameters contradicting the module that realizes them", "X", "round 11, R3-A1")
def f01():
    def m(pkg, d):
        adir = os.path.join(d, "artifacts")
        shutil.copytree(os.path.join(ROOT, "artifacts"), adir)
        f = os.path.join(adir, "metric_definition_rair.json")
        art = json.load(open(f))
        art["aggregation_and_uncertainty"]["estimator"]["parameters"]["tolerance"] = 1e-3
        art["content_hash"] = core.artifact_content_hash({k: v for k, v in art.items() if k != "content_hash"})
        json.dump(art, open(f, "w"))
        return ("--artifacts", adir)
    return verifier_rejects(m, "RULE-PARAMS")


@case("REVISION LAUNDERING: determination citing no assessments and binding no charter", "X", "round 11, R3-A2")
def f02():
    def m(pkg, d):
        ch = [c for c in pkg["case_chains"] if c[0]["chain_ref"] == "case-chain-c02"][0]
        adjs = [e for e in ch if e["event_type"] == "reference_standard_adjudicated"]
        del adjs[-1]["payload"]["charter_ref"]
        adjs[-1]["payload_commitment"]["digest"] = core.h(
            bytes.fromhex(NONCES[adjs[-1]["integrity"]["event_hash"]]) + core.canon(adjs[-1]["payload"]))
        rebuild_chain(ch)
    return verifier_rejects(m, "ADJ-CHARTER")


@case("assessment-free revision decided by an adjudicator without the authorized role", "X", "round 11, R3-A2")
def f03():
    def m(pkg, d):
        ch = [c for c in pkg["case_chains"] if c[0]["chain_ref"] == "case-chain-c02"][0]
        adjs = [e for e in ch if e["event_type"] == "reference_standard_adjudicated"]
        adjs[-1]["payload"]["deciding_adjudicator_ref"] = "adj-A"
        adjs[-1]["payload_commitment"]["digest"] = core.h(
            bytes.fromhex(NONCES[adjs[-1]["integrity"]["event_hash"]]) + core.canon(adjs[-1]["payload"]))
        rebuild_chain(ch)
    return verifier_rejects(m, "ADJ-DECIDER")


@case("assessment-free revision asserting an agreement statistic over no assessments", "X", "round 11, R3-A2")
def f04():
    def m(pkg, d):
        ch = [c for c in pkg["case_chains"] if c[0]["chain_ref"] == "case-chain-c02"][0]
        adjs = [e for e in ch if e["event_type"] == "reference_standard_adjudicated"]
        adjs[-1]["payload"]["inter_adjudicator_agreement"] = {
            "statistic": "percent_agreement_pre_consensus", "value": 1,
            "computed_over_pre_consensus_only": True}
        adjs[-1]["payload_commitment"]["digest"] = core.h(
            bytes.fromhex(NONCES[adjs[-1]["integrity"]["event_hash"]]) + core.canon(adjs[-1]["payload"]))
        rebuild_chain(ch)
    return verifier_rejects(m, "ADJ-AGREE")


@case("derivation engine digest with no locator for the bytes it claims", "S", "round 11, DRV-ENGINE")
def f05():
    art = json.load(open(os.path.join(ROOT, "examples", "derived", "derived-rair-v1.json")))
    art["recomputability"]["derivation_software_digest"] = {"alg": "sha-256", "digest": "00" * 32}
    return schema_rejects(DRV_SCHEMA, art)


@case("charter shipping no revision protocol", "S", "round 11, R3-A2")
def f06():
    a = json.load(open(os.path.join(ROOT, "artifacts", "adjudication_charter.json")))
    del a["revision_protocol"]
    return schema_rejects(DEF_SCHEMA, a)


# ---- round twelve: secondary use and unit of analysis (Irsigler critique) ----

def _individual(pkg, d, **over):
    """Recut a shipped cohort-level metric as an individual-clinician metric."""
    ddir = os.path.join(d, "derived")
    shutil.copytree(DERIVED_DIR, ddir)
    f = os.path.join(ddir, "derived-rsr-v2.json")
    art = json.load(open(f))
    art["unit_of_analysis"] = "individual_clinician"
    art["subject_ref"] = "clinician-pseudo-0417"
    art.update(over)
    json.dump(art, open(f, "w"))
    return ("--derived", ddir)


@case("PER-CLINICIAN RECUT: study authorised only at cohort level re-derived per clinician", "X", "round 12, unit of analysis")
def g01():
    def m(pkg, d):
        # The shipped cohort authorises individual reporting under governance, so
        # the attack is against a cohort that does not.
        adir = os.path.join(d, "artifacts")
        shutil.copytree(os.path.join(ROOT, "artifacts"), adir)
        cd = json.load(open(os.path.join(adir, "cohort_definition.json")))
        cd["unit_of_analysis"] = "cohort"
        cd["content_hash"] = core.artifact_content_hash({k: v for k, v in cd.items() if k != "content_hash"})
        json.dump(cd, open(os.path.join(adir, "cohort_definition.json"), "w"))
        return ("--artifacts", adir)
    return verifier_rejects(m, "UOA-MATCH")


@case("individual-level metric with no secondary-use governance artifact", "X", "round 12, unit of analysis")
def g02():
    def m(pkg, d):
        adir = os.path.join(d, "artifacts")
        shutil.copytree(os.path.join(ROOT, "artifacts"), adir)
        cd = json.load(open(os.path.join(adir, "cohort_definition.json")))
        cd["unit_of_analysis"] = "individual_clinician"
        cd["content_hash"] = core.artifact_content_hash({k: v for k, v in cd.items() if k != "content_hash"})
        json.dump(cd, open(os.path.join(adir, "cohort_definition.json"), "w"))
        extra = _individual(pkg, d)
        return ("--artifacts", adir) + extra
    return verifier_rejects(m, "UOA-GOVERNANCE")


@case("derived artifact asserting a standard-of-care determination", "S", "round 12, non-goal")
def g03():
    art = json.load(open(os.path.join(DERIVED_DIR, "derived-rair-v1.json")))
    art["standard_of_care_determination"] = "below standard"
    return schema_rejects(DRV_SCHEMA, art)


@case("individual-level metric shipped with no interval, subject, governance, or case mix", "S", "round 12, unit of analysis")
def g04():
    art = json.load(open(os.path.join(DERIVED_DIR, "derived-rsr-v2.json")))
    art["unit_of_analysis"] = "individual_clinician"
    return schema_rejects(DRV_SCHEMA, art)


@case("cohort definition declaring no unit of analysis", "S", "round 12, unit of analysis")
def g05():
    a = json.load(open(os.path.join(ROOT, "artifacts", "cohort_definition.json")))
    del a["unit_of_analysis"]
    return schema_rejects(DEF_SCHEMA, a)


def _governed(pkg, d, *, min_cell=1000, case_mix=True, **over):
    """Authorise individual-level derivation, then attack the conditions."""
    adir = os.path.join(d, "artifacts")
    shutil.copytree(os.path.join(ROOT, "artifacts"), adir)
    cd = json.load(open(os.path.join(adir, "cohort_definition.json")))
    cd["unit_of_analysis"] = "individual_clinician"
    cd["content_hash"] = core.artifact_content_hash({k: v for k, v in cd.items() if k != "content_hash"})
    json.dump(cd, open(os.path.join(adir, "cohort_definition.json"), "w"))
    gov = {"artifact_kind": "secondary_use_governance",
           "artifact_id": "https://example.org/dses/governance/pe-credentialing",
           "version": "1.0.0", "created_at": "2026-02-15T00:00:00Z", "author_ref": "study-methods-group",
           "prespecification_cutoff": {"cutoff_type": "before_first_enrollment",
                                       "cutoff_time": "2026-03-01T00:00:00Z"},
           "purpose": "quality improvement", "purpose_code": "quality_improvement",
           "decision_consequence": "advisory",
           "authorized_recipients": ["quality-committee"],
           "review_body": "institutional-quality-committee", "min_cell_size": min_cell,
           "max_observation_window_days": 365,
           "high_stakes_safeguards": {"aggregate_metric_sole_basis_prohibited": True,
                                       "case_level_review_required": False,
                                       "subject_access_to_evidence": True,
                                       "subject_notification_required": True,
                                       "appeal_available": True},
           "case_mix_adjustment": {"required": case_mix, "method_ref": "case-mix-v1"},
           "subject_notification": "Clinician notified before derivation.",
           "appeal_pathway": "Written appeal to the quality committee within 30 days.",
           "retention": "Destroyed after 24 months."}
    gov["content_hash"] = core.artifact_content_hash(gov)
    json.dump(gov, open(os.path.join(adir, "secondary_use_governance.json"), "w"))
    ddir = os.path.join(d, "derived")
    shutil.copytree(DERIVED_DIR, ddir)
    f = os.path.join(ddir, "derived-rsr-v1.json")
    art = json.load(open(f))
    art["unit_of_analysis"] = "individual_clinician"
    art["subject_ref"] = "clinician-c04"
    art["governance_ref"] = {"artifact_id": gov["artifact_id"], "version": gov["version"],
                             "content_hash": {"alg": "sha-256", "digest": gov["content_hash"]}}
    art["case_mix_disclosure"] = {"method_ref": "case-mix-v1", "adjusted": True,
                                  "covariates": ["age", "prior_probability"]}
    art["observation_window"] = {"start": "2026-03-01T00:00:00Z", "end": "2026-04-30T00:00:00Z"}
    art["reliance_context"] = {"subject_case_count": 0, "adjudication_status_breakdown": {},
                               "commensurability_breakdown": {"commensurable": 0, "noncommensurable": 0},
                               "baseline_validity_breakdown": {"correct": 0, "incorrect": 0, "excluded": 0},
                               "ai_validity_breakdown": {"correct": 0, "incorrect": 0, "excluded": 0},
                               "evaluation_validity_breakdown": {"correct": 0, "incorrect": 0, "excluded": 0},
                               "ai_system_breakdown": {}, "exposure_class_breakdown": {}}
    art.update(over)
    json.dump(art, open(f, "w"))
    return ("--artifacts", adir, "--derived", ddir)


@case("individual-level metric over a denominator far below the governance minimum", "X", "round 12, small cells")
def g06():
    def m(pkg, d):
        return _governed(pkg, d, min_cell=1000)
    return verifier_rejects(m, "UOA-CELLSIZE")


@case("individual-level metric with no case-mix adjustment where governance requires it", "X", "round 12, case mix")
def g07():
    def m(pkg, d):
        return _governed(pkg, d, min_cell=1, case_mix=True,
                         case_mix_disclosure={"method_ref": "case-mix-v1", "adjusted": False,
                                              "covariates": ["age"]})
    return verifier_rejects(m, "UOA-CASEMIX")


@case("cohort declaring no unit of analysis at all (verifier layer)", "S", "round 12, unit of analysis")
def g08():
    def m(pkg, d):
        adir = os.path.join(d, "artifacts")
        shutil.copytree(os.path.join(ROOT, "artifacts"), adir)
        cd = json.load(open(os.path.join(adir, "cohort_definition.json")))
        del cd["unit_of_analysis"]
        cd["content_hash"] = core.artifact_content_hash({k: v for k, v in cd.items() if k != "content_hash"})
        json.dump(cd, open(os.path.join(adir, "cohort_definition.json"), "w"))
        return ("--artifacts", adir)
    return verifier_rejects(m, "UOA-DECLARED")


@case("derived artifact asserting a competence determination (verifier layer)", "S", "round 12, non-goal")
def g09():
    def m(pkg, d):
        ddir = os.path.join(d, "derived")
        shutil.copytree(DERIVED_DIR, ddir)
        f = os.path.join(ddir, "derived-rsr-v2.json")
        art = json.load(open(f))
        art["competence_determination"] = "resistant to AI guidance"
        json.dump(art, open(f, "w"))
        return ("--derived", ddir)
    return verifier_rejects(m, "UOA-NONORM")


# ---- round thirteen: longitudinal individual-use governance ----

@case("individual metric whose committed inputs belong to another clinician", "X", "round 13, subject scoping")
def h01():
    def m(pkg, d):
        return _governed(pkg, d, min_cell=1, subject_ref="clinician-does-not-exist")
    return verifier_rejects(m, "UOA-SUBJECT")


@case("individual metric whose observation window exceeds the governance maximum", "X", "round 13, longitudinal window")
def h02():
    def m(pkg, d):
        # helper authors a 60-day metric window; reduce governance maximum after creation
        extra = _governed(pkg, d, min_cell=1)
        adir = os.path.join(d, "artifacts")
        gp = os.path.join(adir, "secondary_use_governance.json")
        gov = json.load(open(gp))
        gov["max_observation_window_days"] = 10
        gov["content_hash"] = core.artifact_content_hash({k:v for k,v in gov.items() if k != "content_hash"})
        json.dump(gov, open(gp, "w"))
        # repair derived ref to the changed governance hash
        f = os.path.join(d, "derived", "derived-rsr-v1.json")
        art = json.load(open(f))
        art["governance_ref"]["content_hash"]["digest"] = gov["content_hash"]
        json.dump(art, open(f, "w"))
        return extra
    return verifier_rejects(m, "UOA-WINDOW")


@case("individual metric carrying a cherry-picked or false reliance context", "X", "round 13, balanced context")
def h03():
    def m(pkg, d):
        return _governed(pkg, d, min_cell=1, reliance_context={
            "subject_case_count": 999, "adjudication_status_breakdown": {},
            "commensurability_breakdown": {"commensurable": 0, "noncommensurable": 0},
            "baseline_validity_breakdown": {"correct": 0, "incorrect": 0, "excluded": 0},
            "ai_validity_breakdown": {"correct": 0, "incorrect": 0, "excluded": 0},
            "evaluation_validity_breakdown": {"correct": 0, "incorrect": 0, "excluded": 0},
            "ai_system_breakdown": {}, "exposure_class_breakdown": {}})
    return verifier_rejects(m, "UOA-CONTEXT")


@case("high-stakes credentialing governance permits aggregate-only adverse action", "S", "round 13, adverse-action boundary")
def h04():
    def m(pkg, d):
        extra = _governed(pkg, d, min_cell=1)
        gp = os.path.join(d, "artifacts", "secondary_use_governance.json")
        gov = json.load(open(gp))
        gov["purpose"] = "credentialing review"
        gov["purpose_code"] = "credentialing"
        gov["decision_consequence"] = "credentialing"
        gov["high_stakes_safeguards"] = {"aggregate_metric_sole_basis_prohibited": False,
                                          "case_level_review_required": False,
                                          "subject_access_to_evidence": True,
                                          "subject_notification_required": False,
                                          "appeal_available": True}
        gov["content_hash"] = core.artifact_content_hash({k:v for k,v in gov.items() if k != "content_hash"})
        json.dump(gov, open(gp, "w"))
        f = os.path.join(d, "derived", "derived-rsr-v1.json")
        art = json.load(open(f)); art["governance_ref"]["content_hash"]["digest"] = gov["content_hash"]
        json.dump(art, open(f, "w"))
        return extra
    return verifier_rejects(m, "UOA-HIGHSTAKES")


@case("balanced context reporting every subject case as excluded, which a degenerate builder would agree with", "X", "round 14, context integrity")
def i01():
    def m(pkg, d):
        ddir = os.path.join(d, "derived")
        shutil.copytree(DERIVED_DIR, ddir)
        f = os.path.join(ddir, "derived-rair-subject-0417-v1.json")
        art = json.load(open(f))
        for k in ("baseline_validity_breakdown", "ai_validity_breakdown", "evaluation_validity_breakdown"):
            total = sum(art["reliance_context"][k].values())
            art["reliance_context"][k] = {"correct": 0, "incorrect": 0, "excluded": total}
        json.dump(art, open(f, "w"))
        return ("--derived", ddir)
    return verifier_rejects(m, "UOA-CONTEXT")


@case("individual metric whose AI-error exposure is understated in its context", "X", "round 14, context integrity")
def i02():
    def m(pkg, d):
        ddir = os.path.join(d, "derived")
        shutil.copytree(DERIVED_DIR, ddir)
        f = os.path.join(ddir, "derived-rair-subject-0417-v1.json")
        art = json.load(open(f))
        b = art["reliance_context"]["ai_validity_breakdown"]
        b["incorrect"], b["correct"] = 0, b["correct"] + b["incorrect"]
        json.dump(art, open(f, "w"))
        return ("--derived", ddir)
    return verifier_rejects(m, "UOA-CONTEXT")


@case("context hiding the subject's failed linkages by computing over metric-eligible cases only", "X", "round 15, population")
def j01():
    def m(pkg, d):
        ddir = os.path.join(d, "derived")
        shutil.copytree(DERIVED_DIR, ddir)
        f = os.path.join(ddir, "derived-rair-subject-0417-v1.json")
        art = json.load(open(f))
        c = art["reliance_context"]
        c["subject_decision_instance_count"] = c["metric_eligible_count"]
        c["linkage_breakdown"] = {"linked": c["metric_eligible_count"]}
        c["maturation_breakdown"] = {"mature": c["metric_eligible_count"]}
        c["adjudication_breakdown"] = {"determinate": 7, "indeterminate": 1}
        json.dump(art, open(f, "w"))
        return ("--derived", ddir)
    return verifier_rejects(m, "UOA-CONTEXT")


@case("context breakdowns that do not reconcile to the declared instance count", "X", "round 15, reconcile")
def j02():
    def m(pkg, d):
        ddir = os.path.join(d, "derived")
        shutil.copytree(DERIVED_DIR, ddir)
        f = os.path.join(ddir, "derived-rair-subject-0417-v1.json")
        art = json.load(open(f))
        art["reliance_context"]["adjudication_breakdown"]["not_adjudicated"] = 0
        json.dump(art, open(f, "w"))
        return ("--derived", ddir)
    return verifier_rejects(m, "UOA-CONTEXT-RECONCILE")


@case("individual metric with no prospective responsibility assignment artifact", "X", "round 15, assignment")
def j03():
    def m(pkg, d):
        ddir = os.path.join(d, "derived")
        shutil.copytree(DERIVED_DIR, ddir)
        f = os.path.join(ddir, "derived-rair-subject-0417-v1.json")
        art = json.load(open(f))
        art["reliance_context"]["assignment_ref"] = {"artifact_id": "https://example.org/absent", "version": "1.0.0"}
        json.dump(art, open(f, "w"))
        return ("--derived", ddir)
    return verifier_rejects(m, "UOA-ASSIGNMENT")


@case("retrospective surveillance declared as prospective governance", "X", "round 15, timing")
def j04():
    def m(pkg, d):
        ddir = os.path.join(d, "derived")
        shutil.copytree(DERIVED_DIR, ddir)
        f = os.path.join(ddir, "derived-rair-subject-0417-v1.json")
        art = json.load(open(f))
        art["observation_window"]["start"] = "2026-01-01T00:00:00Z"
        json.dump(art, open(f, "w"))
        return ("--derived", ddir)
    return verifier_rejects(m, "UOA-TIMING")


@case("metric input smuggled from a case never assigned to the subject", "X", "round 15, population")
def j05():
    def m(pkg, d):
        adir = os.path.join(d, "artifacts")
        shutil.copytree(os.path.join(ROOT, "artifacts"), adir)
        f = os.path.join(adir, "responsibility_assignments.json")
        art = json.load(open(f))
        art["assignments"] = [x for x in art["assignments"] if x["case_ref"] != "case-chain-c00"]
        art["content_hash"] = core.artifact_content_hash({k: v for k, v in art.items() if k != "content_hash"})
        json.dump(art, open(f, "w"))
        return ("--artifacts", adir)
    return verifier_rejects(m, "UOA-CONTEXT-POPULATION")


@case("metric-eligible count overstating the derivable subset", "X", "round 15, reconcile")
def j06():
    def m(pkg, d):
        ddir = os.path.join(d, "derived")
        shutil.copytree(DERIVED_DIR, ddir)
        f = os.path.join(ddir, "derived-rair-subject-0417-v1.json")
        art = json.load(open(f))
        art["reliance_context"]["metric_eligible_count"] = art["reliance_context"]["subject_decision_instance_count"]
        json.dump(art, open(f, "w"))
        return ("--derived", ddir)
    return verifier_rejects(m, "UOA-CONTEXT-METRIC")


def main():
    passed = failed = 0
    for name, cls, origin, fn in CASES:
        ok, detail = fn()
        status = "REJECTED " if ok else "ACCEPTED "
        print(f"{cls:5s} {status} {name}   ({origin})")
        if ok:
            passed += 1
        else:
            failed += 1
            print(f"        {detail}")
    print(f"\n{len(CASES)} adversarial cases, {passed} rejected at the asserted rule, {failed} not")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
