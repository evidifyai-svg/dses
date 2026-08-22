#!/usr/bin/env python3
"""dses-verify: the DSES v0.2.0 reference verifier.

Release-build properties, each closing a finding from external review:

  * Trust roots are EXTERNAL. Anchor receipts verify only against keys in the
    reader-supplied trust store (--anchor-trust). Keys carried inside the
    package never authenticate anchors, because the package is rewritable by
    its operator (threat model A1).
  * Executable rules are LOADED AND EXECUTED. Every code_artifact_digest is
    recomputed from the module bytes, the module's shipped conformance
    fixtures are run, and metrics are recomputed by executing those modules,
    not by consulting a parallel implementation of their semantics.
  * Recomputation is AGAINST THE SNAPSHOT. Case chains are truncated to the
    sequences frozen in the snapshot's population tuples before adjudication
    state is replayed, so a superseded v1 metric verifies against the evidence
    that existed when it was derived.
  * Every check carries a stable rule identifier, printed on failure, so the
    regression suite can assert WHICH rule rejected a package.

Usage:
  python3 scripts/dses_verify.py [package.json] [--witness FILE]
      [--anchor-trust FILE] [--profile OL] [--quiet]
"""
import argparse
import datetime as dt
import importlib.util
import json
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dses_core import (  # noqa: E402
    anchor_receipt_target, artifact_content_hash, canon, event_preimage_hash,
    file_digest, h, mth, signing_input, verify_consistency, verify_dses, verify_inclusion,
    wilson_interval,
)
from dses_derivation import recompute_metric  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HIDING_REQUIRED = {"adjudicator_assessment_committed", "reference_standard_adjudicated"}
TERMINAL_LINKAGE = {"linked", "ambiguous", "failed", "decision_record_missing", "outcome_record_missing", "withdrawn"}
V01_EVENT_TYPES = {"case_opened", "preliminary_read_committed", "ai_output_released",
                   "post_exposure_read_committed", "final_decision_committed"}


def iso(s):
    try:
        return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
    except (ValueError, AttributeError, TypeError):
        return None


def dur_days(d):
    m = re.fullmatch(r"P(?:(\d+)Y)?(?:(\d+)M)?(?:(\d+)W)?(?:(\d+)D)?", d or "")
    if not m:
        return None
    y, mo, w, dd = (int(x) if x else 0 for x in m.groups())
    return y * 365 + mo * 31 + w * 7 + dd


class Report:
    def __init__(self, quiet=False):
        self.n, self.failures, self.attestations, self.quiet = 0, [], [], quiet

    def check(self, ok, label, cls="C", rule="GEN"):
        self.n += 1
        if not ok:
            self.failures.append((rule, label))
        if not self.quiet:
            print(f"  [{cls}] {'PASS' if ok else 'FAIL'}  ({rule}) {label}")
        return bool(ok)

    def attest(self, label):
        if label not in self.attestations:
            self.attestations.append(label)

    def section(self, t):
        if not self.quiet:
            print(f"\n{t}")


def load_rule(rule_id):
    path = os.path.join(ROOT, "rules", rule_id.replace("-", "_") + ".py")
    spec = importlib.util.spec_from_file_location(rule_id.replace("-", "_"), path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod, path


class Resolver:
    def __init__(self, r, directory, label):
        self.r, self.label = r, label
        self.by_id, self.duplicates, self.objects = {}, [], []
        if not os.path.isdir(directory):
            return
        for fn in sorted(os.listdir(directory)):
            if not fn.endswith(".json"):
                continue
            obj = json.load(open(os.path.join(directory, fn)))
            recomputed = artifact_content_hash({k: v for k, v in obj.items() if k not in ("content_hash", "artifact_hash")})
            stored = obj.get("content_hash") or obj.get("artifact_hash")
            r.check(recomputed == stored, f"{label} {fn}: content hash recomputes", "C", "ART-HASH")
            key = (obj.get("artifact_id"), obj.get("version", "1.0.0"))
            if key in self.by_id:
                self.duplicates.append(key)
            self.by_id[key] = (fn, obj, recomputed)
            self.objects.append((fn, obj, recomputed))
        r.check(not self.duplicates, f"{label}: identifiers resolve uniquely", "X", "ART-UNIQUE")

    def resolve(self, ref, where):
        key = (ref.get("artifact_id"), ref.get("version"))
        hit = self.by_id.get(key)
        if not self.r.check(hit is not None, f"{where}: reference {key[0]} v{key[1]} resolves", "X", "REF-RESOLVE"):
            return None
        want = ref.get("content_hash", {}).get("digest")
        self.r.check(hit[2] == want, f"{where}: referenced content hash matches the resolved artifact", "C", "REF-HASH")
        return hit[1]


def verify_chain(events, r, name, scope):
    prev, prev_seq, ids = None, -1, set()
    for ev in events:
        eid = ev["event_id"]
        r.check(eid not in ids, f"{name}/{eid}: event identifier unique in chain", "X", "EVT-UNIQUE")
        ids.add(eid)
        r.check(event_preimage_hash(ev) == ev["integrity"]["event_hash"],
                f"{name}/{eid}: event hash recomputes from its RFC 8785 preimage", "C", "EVT-HASH")
        if prev is None:
            r.check("prev_event_hash" not in ev["integrity"], f"{name}/{eid}: genesis carries no predecessor", "C", "CHAIN-GENESIS")
        else:
            r.check(ev["integrity"].get("prev_event_hash") == prev, f"{name}/{eid}: links to predecessor", "C", "CHAIN-LINK")
        r.check(ev["sequence"] == prev_seq + 1, f"{name}/{eid}: sequence contiguous", "C", "CHAIN-SEQ")
        r.check(iso(ev["occurred_at"]) is not None and iso(ev["recorded_at"]) is not None,
                f"{name}/{eid}: timestamps are real instants", "X", "EVT-TIME")
        if scope:
            r.check(ev["chain_scope"] == scope, f"{name}/{eid}: chain scope matches", "X", "EVT-SCOPE")
        prev, prev_seq = ev["integrity"]["event_hash"], ev["sequence"]
    return prev


def verify_commitments(events, nonces, r, name):
    for ev in events:
        eid, pc = ev["event_id"], ev.get("payload_commitment")
        if pc is None:
            r.check(False, f"{name}/{eid}: event carries a payload commitment", "S", "PC-PRESENT")
            continue
        if ev["event_type"] in HIDING_REQUIRED:
            r.check(pc["commitment_type"] == "hiding", f"{name}/{eid}: low-entropy payload uses a hiding commitment", "X", "PC-HIDING")
        if "payload" not in ev:
            continue
        cp = canon(ev["payload"])
        if pc["commitment_type"] == "content_digest":
            r.check(h(cp) == pc["digest"], f"{name}/{eid}: content commitment matches payload", "C", "PC-CONTENT")
        else:
            nonce = nonces.get(ev["integrity"]["event_hash"])
            nonce_bytes = None
            try:
                nonce_bytes = bytes.fromhex(nonce) if nonce is not None else None
            except (ValueError, TypeError):
                nonce_bytes = None
            r.check(nonce_bytes is not None and len(nonce_bytes) * 8 == pc.get("nonce_bits")
                    and len(nonce_bytes) * 8 >= 128,
                    f"{name}/{eid}: nonce encoding matches nonce_bits and is at least 128 bits",
                    "X", "PC-NONCE-LENGTH")
            r.check(nonce_bytes is not None and h(nonce_bytes + cp) == pc["digest"],
                    f"{name}/{eid}: hiding commitment matches payload under its nonce", "C", "PC-NONCE")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("package", nargs="?", default=os.path.join(ROOT, "examples", "example-package.json"))
    ap.add_argument("--nonces", default=os.path.join(ROOT, "examples", "nonce-store.json"))
    ap.add_argument("--artifacts", default=os.path.join(ROOT, "artifacts"))
    ap.add_argument("--derived", default=os.path.join(ROOT, "examples", "derived"))
    ap.add_argument("--sequences", default=os.path.join(ROOT, "examples", "decision-sequences"))
    ap.add_argument("--fixtures", default=os.path.join(ROOT, "fixtures"),
                    help="directory of rule and signature-profile conformance fixtures")
    ap.add_argument("--anchor-trust", default=None, help="reader-supplied external anchor trust store")
    ap.add_argument("--witness", default=None)
    ap.add_argument("--profile", default="OL")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()

    pkg = json.load(open(a.package))
    nonces = json.load(open(a.nonces))["nonces"] if os.path.exists(a.nonces) else {}
    r = Report(a.quiet)
    profile = {}
    cohort, case_chains = pkg["cohort_chain"], pkg["case_chains"]

    def cev(t):
        return [e for e in cohort if e["event_type"] == t]

    # ------------------------------------------------------------ trust roots
    r.section("trust roots (external to the package)")
    trust = json.load(open(a.anchor_trust)) if a.anchor_trust and os.path.exists(a.anchor_trust) else {"authorities": {}}
    anchor_keys = {ident: v["public_key"] for ident, v in trust.get("authorities", {}).items()}
    r.check(bool(anchor_keys), "an external anchor trust store is supplied; package-carried anchor keys are never trusted",
            "X", "TRUST-EXTERNAL")

    r.section("signature profile self-test")
    tv_path = os.path.join(a.fixtures, "dses-sig-v1.testvectors.json")
    if os.path.exists(tv_path):
        tv = json.load(open(tv_path))
        ok = True
        for v in tv["vectors"]:
            si = signing_input(v["context_label"], v["target_hash"])
            if si.hex() != v["signing_input_hex"]:
                ok = False
            probe = {"profile": "DSES-SIG-v1", "alg": "ed25519", "key_ref": "test-key-1",
                     "context_label": v["context_label"], "target_hash": v["target_hash"],
                     "value": v["signature_value"]}
            if not verify_dses(probe, tv["public_key_hex"]):
                ok = False
        r.check(ok, f"DSES-SIG-v1 statement encoding matches all {len(tv['vectors'])} shipped test vectors",
                "C", "SIG-VECTORS")
    else:
        r.check(False, "DSES-SIG-v1 test vectors ship with the package", "C", "SIG-VECTORS")

    r.section("chain integrity")
    cohort_head = verify_chain(cohort, r, "cohort", "cohort")
    verify_commitments(cohort, nonces, r, "cohort")
    heads, chain_refs = {}, Counter()
    for ch in case_chains:
        ref = ch[0]["chain_ref"]
        chain_refs[ref] += 1
        heads[ref] = verify_chain(ch, r, ref, "case")
        verify_commitments(ch, nonces, r, ref)
    r.check(all(v == 1 for v in chain_refs.values()), "case chain references unique", "X", "CHAIN-UNIQUE")

    # Event signatures are optional, but every one present is normative evidence
    # and must verify. Verification occurs after the committed key directory is
    # reconstructed below; the events are retained for that pass.

    # ------------------------------------------------------------ key authority
    r.section("key authority")
    genesis = cev("cohort_chain_created")
    r.check(len(genesis) == 1, "exactly one cohort genesis", "X", "GENESIS-ONE")
    directory = genesis[0]["payload"]["key_directory"] if genesis else []
    refs = [k["key_ref"] for k in directory]
    r.check(len(refs) == len(set(refs)), "no duplicate key references in the committed directory", "X", "KEY-UNIQUE")
    keys = {k["key_ref"]: k for k in directory}
    r.check("key_directory" not in pkg, "no uncommitted top-level key directory", "X", "KEY-COMMITTED")
    revoked = {}
    for e in cev("key_revoked") + cev("key_compromise_declared"):
        revoked[e["payload"]["key_ref"]] = e["payload"].get("effective_at", e["occurred_at"])
    for e in cev("key_rotated"):
        revoked.setdefault(e["payload"]["retired_key_ref"], e["payload"]["effective_at"])

    def key_usable(key_ref, when):
        k = keys.get(key_ref)
        if not k:
            return False, "unknown key reference"
        t = iso(when)
        if k.get("valid_from") and t < iso(k["valid_from"]):
            return False, "before validity"
        if k.get("valid_to") and t > iso(k["valid_to"]):
            return False, "after validity"
        if key_ref in revoked and t > iso(revoked[key_ref]):
            return False, "after retirement or revocation"
        return True, "usable"

    def check_sig(sig, target, when, where, expected_context):
        profile_ok = (isinstance(sig, dict) and sig.get("profile") == "DSES-SIG-v1"
                      and sig.get("alg") == "ed25519" and sig.get("context_label") == expected_context)
        r.check(profile_ok, f"{where}: signature declares DSES-SIG-v1/ed25519 under context {expected_context}",
                "S", "SIG-PROFILE")
        key_ref = sig.get("key_ref") if isinstance(sig, dict) else None
        ok_key, why = key_usable(key_ref, when) if key_ref else (False, "missing key reference")
        r.check(ok_key, f"{where}: key status at signing time ({why})", "X", "SIG-KEYTIME")
        r.check(isinstance(sig, dict) and sig.get("target_hash") == target,
                f"{where}: signature targets its object", "C", "SIG-TARGET")
        r.check(profile_ok and verify_dses(sig, keys.get(key_ref, {}).get("public_key", "")),
                f"{where}: signature verifies under DSES-SIG-v1", "C", "SIG-VERIFY")

    def event_sig_context(ev):
        if ev["event_type"] == "checkpoint_committed":
            return "checkpoint"
        if ev["event_type"] == "adjudicator_assessment_committed":
            return "assessment"
        return "event"

    for chain_name, chain in [("cohort", cohort)] + [(ch[0]["chain_ref"], ch) for ch in case_chains]:
        for ev in chain:
            for i, sig in enumerate(ev.get("signatures", [])):
                check_sig(sig, ev["integrity"]["event_hash"], ev["occurred_at"],
                          f"{chain_name}/{ev['event_id']} signature {i}", event_sig_context(ev))

    # ------------------------------------------------------------ anchors
    r.section("anchor evidence (verified against the external trust root only)")
    verified_anchors = {}
    for e in cev("anchor_evidence_recorded"):
        p = e["payload"]
        body, sig = p["receipt_body"], p["receipt_signature"]
        pub = anchor_keys.get(body["tsa_identity"], "")
        ok = (sig.get("profile") == "DSES-SIG-v1"
              and sig.get("alg") == "ed25519"
              and sig.get("context_label") == "anchor-receipt"
              and anchor_receipt_target(body) == sig.get("target_hash")
              and body["artifact_hash"] == p["artifact_hash"]
              and verify_dses(sig, pub))
        r.check(ok, f"anchor for {p['artifact_id']}: receipt binds artifact, time, and authority, and verifies under the EXTERNAL trust root",
                "C", "ANCHOR-RECEIPT")
        if ok:
            verified_anchors[p["artifact_hash"]] = body["anchor_time"]
    r.attest("Anchor authority honesty and non-equivocation (A7) are trust-policy assumptions")
    distrusted = {e["payload"]["anchor_authority"] for e in cev("anchor_distrusted")}
    r.check(not (distrusted & set(anchor_keys)), "no anchor counted from a distrusted authority", "X", "ANCHOR-DISTRUST")

    # ---------------------------------------------------- executable rule layer
    r.section("executable rules (digests recomputed, fixtures executed)")
    rule_mods = {}

    def bind_rule(exe, where):
        rid = exe["rule_id"]
        # The code artifact is located by its DECLARED locator. A path convention
        # private to one implementation is not a specification (round 10, item 3).
        ca = exe.get("code_artifact")
        if ca and ca.get("locator"):
            path = os.path.join(ROOT, ca["locator"])
        else:
            path = os.path.join(ROOT, "rules", rid.replace("-", "_") + ".py")
        if not r.check(os.path.exists(path), f"{where}: rule {rid} resolves to code", "X", "RULE-RESOLVE"):
            return None
        want_digest = (ca or {}).get("digest", {}).get("digest")
        r.check(file_digest(path) == want_digest,
                f"{where}: rule {rid} code digest matches the module bytes", "C", "RULE-DIGEST")
        fx = os.path.join(ROOT, exe["fixtures_ref"])
        r.check(os.path.exists(fx), f"{where}: rule {rid} fixtures resolve", "X", "RULE-FIXTURES")
        if rid not in rule_mods:
            rule_mods[rid], _ = load_rule(rid)
            fxdoc = json.load(open(fx)) if os.path.exists(fx) else {}
            vecs = list(fxdoc.get("vectors", [])) + list(fxdoc.get("interval_vectors", []))
            ok = True
            m = rule_mods[rid]
            for v in vecs:
                try:
                    if rid == "pe-projection-v1":
                        got = m.project(v["events"])
                        ok &= all(got.get(k) == vv for k, vv in v["expect"].items())
                    elif rid == "pe-binary-v1":
                        ok &= m.classify(v["judgment"], v["conclusion"]) == v["expect"]
                    elif rid == "alignment-same-v1":
                        ok &= m.aligns(v["evaluation"], v["ai_output"]) == v["expect"]
                    elif rid == "agreement-percent-v1":
                        ok &= m.agreement(v["assessments"]) == v["expect"]
                    elif rid in ("rair-v1", "rsr-v1", "ear-v1"):
                        ok &= list(m.contributes(v["vb"], v["va"], v["ve"], v["aligned_same"])) == v["expect"]
                    elif rid == "binomial-point-v1":
                        if "expect" in v:
                            ok &= m.estimate(v["n"], v["d"]) == v["expect"]
                        else:
                            got = m.interval(v["n"], v["d"])
                            tol = v.get("tolerance", 1e-9)
                            ok &= (got is not None
                                   and abs(got["lower"] - v["expect_lower"]) <= tol
                                   and abs(got["upper"] - v["expect_upper"]) <= tol)
                    elif rid == "pe-eligibility-v1":
                        ok &= m.eligible(v["encounter"]) == v["expect"]
                    elif rid == "pe-composite-v1":
                        ok &= m.compose(v["imaging"], v["course"]) == v["expect"]
                    elif rid == "pe-decision-v1":
                        ok &= list(m.decide(v["imaging"], v["course"], v["treated_without_confirmation"])) == v["expect"]
                except Exception:
                    ok = False
            r.check(ok, f"rule {rid}: shipped conformance fixtures pass against the loaded module", "X", "RULE-CONFORM")
        return rule_mods[rid]

    # ------------------------------------------------------ definition artifacts
    r.section("definition artifacts")
    defs = Resolver(r, a.artifacts, "definition artifact")
    for fn, obj, digest in defs.objects:
        r.check("anchor" not in obj and "prespecification_assurance" not in obj,
                f"{fn}: no anchor evidence or self-reported assurance inside the hash preimage", "X", "ART-NOANCHOR")
        cutoff = obj.get("prespecification_cutoff", {})
        at = verified_anchors.get(digest)
        r.check(bool(at) and bool(cutoff.get("cutoff_time")) and iso(at) < iso(cutoff["cutoff_time"]),
                f"{fn}: derived as externally anchored before the declared {cutoff.get('cutoff_type', 'cutoff')}",
                "X", "ART-PRESPEC")
        for path, exe in _walk_executables(obj):
            bind_rule(exe, f"{fn}:{path}")

    cohort_def = defs.resolve(genesis[0]["payload"]["cohort_definition_ref"], "genesis cohort definition") if genesis else None
    plan = defs.resolve(genesis[0]["payload"]["analysis_plan_ref"], "genesis analysis plan") if genesis else None
    genesis_set = genesis[0]["payload"].get("definition_set", []) if genesis else []
    for dref in genesis_set:
        defs.resolve(dref, "genesis definition set entry")
    primary_criterion = defs.resolve(cohort_def["evaluation_criteria"]["primary"], "cohort primary criterion") if cohort_def else None
    charter = None
    if primary_criterion:
        charter = defs.resolve(primary_criterion["clinical_reference_standard"]["determination_mechanism"]["adjudication_charter_ref"],
                               "criterion adjudication charter")
    projection_rule = defs.resolve(plan["primary_projection_rule_ref"], "plan projection rule") if plan else None
    proj_mod = bind_rule(projection_rule["executable"], "projection rule") if projection_rule else None
    binary_mod = bind_rule(primary_criterion["binary_validity_projection"]["executable"], "binary projection") if primary_criterion else None

    def in_force_at(seq_index):
        s = {(x["artifact_id"], x["version"]) for x in genesis_set}
        for e in cohort[:seq_index]:
            if e["event_type"] == "definition_set_amended":
                ar = e["payload"]["added_artifact_ref"]
                s.add((ar["artifact_id"], ar["version"]))
        return s

    # ---------------------------------------------- manifests and denominator
    r.section("membership across manifests, and denominator closure")
    manifests = {e["integrity"]["event_hash"]: e for e in cev("eligibility_manifest_committed")}
    r.check(len(manifests) >= 1, "at least one manifest committed", "X", "MAN-PRESENT")
    latency = dur_days((cohort_def or {}).get("manifest_cadence", {}).get("max_latency_after_period_end", "P0D")) or 0
    total_committed = 0
    for mh, me in manifests.items():
        mp = me["payload"]
        body = {k: v for k, v in mp.items() if k != "attestation_signature"}
        check_sig(mp["attestation_signature"], h(canon(body)), me["occurred_at"], f"manifest {mp['period_start'][:10]}", "eligibility-manifest")
        total_committed += mp["manifest_count"]
        lag = (iso(me["occurred_at"]) - iso(mp["period_end"])).days
        r.check(lag <= latency, f"manifest {mp['period_start'][:10]}: committed within the declared latency ({lag}d <= {latency}d)",
                "X", "MAN-LATENCY")

    leaves_seen, positions = [], set()
    for ch in case_chains:
        g, ref = ch[0], ch[0]["chain_ref"]
        r.check(g["event_type"] == "case_track_created", f"{ref}: genesis is a case track", "X", "TRACK-GENESIS")
        p = g["payload"]
        me = manifests.get(p.get("manifest_ref"))
        if not r.check(me is not None, f"{ref}: track binds to a committed manifest by event hash", "X", "TRACK-MANIFEST"):
            continue
        proof = p["manifest_inclusion_proof"]
        r.check(proof["root"] == me["payload"]["eligible_case_commitment_root"],
                f"{ref}: inclusion proof targets its manifest's root", "C", "TRACK-ROOT")
        r.check(verify_inclusion(p["membership_leaf"].encode(), proof["leaf_index"], proof["tree_size"],
                                 proof["audit_path"], proof["root"]),
                f"{ref}: membership leaf verifies at its committed index", "C", "TRACK-INCLUSION")
        leaves_seen.append(p["membership_leaf"])
        positions.add((p["manifest_ref"], proof["leaf_index"]))
    r.check(len(positions) == total_committed,
            f"every committed position across all manifests has a track ({len(positions)}/{total_committed})", "X", "DENOM-CLOSED")
    r.check(len(set(leaves_seen)) == len(leaves_seen), "membership leaves unique across manifests", "X", "DENOM-UNIQUE")
    profile["membership commitment"] = all("eligible_case_commitment_root" in m["payload"] for m in manifests.values())
    profile["all members tracked"] = len(positions) == total_committed
    profile["no duplicate members"] = len(set(leaves_seen)) == len(leaves_seen)

    # -------------------------------------------------- linkage state, replayed
    r.section("linkage state (replayed)")
    track_state, linked_cases = {}, []
    for ch in case_chains:
        ref, state = ch[0]["chain_ref"], "pending"
        for ev in ch:
            if ev["event_type"] == "linkage_attempted":
                r.check("track_state" not in ev["payload"], f"{ref}: attempt records a result only", "S", "LINK-NOSTATE")
                r.check(state in ("pending", "ambiguous"), f"{ref}: attempt from a non-terminal state", "X", "LINK-ORDER")
                state = ev["payload"]["attempt_result"]
            if ev["event_type"] == "linkage_asserted":
                r.check(state == "linked", f"{ref}: linkage asserted only from a replayed linked state", "X", "LINK-ASSERT")
        track_state[ref] = state
        if state == "linked":
            linked_cases.append(ref)
    profile["terminal linkage accounting"] = all(s in TERMINAL_LINKAGE for s in track_state.values())

    # ------------------------------------ v0.1 sequences: resolve, replay, project
    r.section("referenced v0.1 decision sequences (resolved, replayed, commitments verified, projected by the loaded rule)")
    trajectories, index_when = {}, {}
    for ch in case_chains:
        ref = ch[0]["chain_ref"]
        la = [e for e in ch if e["event_type"] == "linkage_asserted"]
        if not la:
            continue
        dr = la[0]["payload"]["decision_sequence_ref"]
        path = os.path.join(a.sequences, os.path.basename(dr["resolver"]))
        if not os.path.exists(path):
            path = os.path.join(ROOT, dr["resolver"])
        if not r.check(os.path.exists(path), f"{ref}: v0.1 sequence resolves", "X", "V01-RESOLVE"):
            continue
        seq = json.load(open(path))
        evs = seq["events"]
        ok_types = all(e["event_type"] in V01_EVENT_TYPES and "payload_commitment" in e and "integrity" in e for e in evs)
        r.check(ok_types, f"{ref}: v0.1 events are structurally well formed with payload commitments", "S", "V01-SHAPE")
        head = verify_chain(evs, r, f"{ref}:v0.1", None)
        verify_commitments(evs, nonces, r, f"{ref}:v0.1")
        r.check(head == dr["sequence_head_hash"], f"{ref}: v0.1 head hash matches the bound reference", "C", "V01-HEAD")
        finals = [e for e in evs if e["event_type"] == "final_decision_committed"]
        r.check(len(finals) == 1 and finals[0]["integrity"]["event_hash"] == dr["final_decision_hash"]
                and finals[0] is evs[-1],
                f"{ref}: bound final decision belongs to and terminates the sequence", "C", "V01-FINAL")
        if finals:
            index_when[ref] = finals[0]["occurred_at"]
        if proj_mod:
            proj = proj_mod.project(evs)
            ok = proj is not None and "excluded" not in (proj or {})
            r.check(ok, f"{ref}: the declared projection rule executes over the sequence, which is what establishes baseline-before-exposure-before-evaluation ordering", "X", "V01-PROJECT")
            if ok:
                if projection_rule.get("actor_identity_requirement") == "baseline_equals_evaluation_actor":
                    r.check(proj["baseline_actor"] == proj["evaluation_actor"],
                            f"{ref}: actor identity condition holds", "X", "V01-ACTOR")
                trajectories[ref] = proj
    profile["v0.1 sequences resolve and verify"] = all(ref in trajectories for ref in linked_cases)

    # -------------------------------------- adjudication: DAG, charter, agreement
    r.section("adjudication (lineage, charter, agreement)")
    adj_events = {}
    for ch in case_chains:
        ref = ch[0]["chain_ref"]
        assess = {e["integrity"]["event_hash"]: e for e in ch if e["event_type"] == "adjudicator_assessment_committed"}
        roster = {x["adjudicator_ref"] for x in (charter or {}).get("roster", [])}
        for ev in ch:
            if ev["event_type"] == "adjudicator_assessment_committed" and charter:
                defs.resolve(ev["payload"]["charter_ref"], f"{ref} assessment charter")
                r.check(ev["payload"]["adjudicator_ref"] in roster,
                        f"{ref}: assessing adjudicator is on the charter roster", "X", "ADJ-ROSTER")
            if ev["event_type"] != "reference_standard_adjudicated":
                continue
            p = ev["payload"]
            if primary_criterion:
                cref = p["evaluation_criterion_ref"]
                r.check((cref["artifact_id"], cref["version"]) in
                        {(x["artifact_id"], x["version"]) for x in [cohort_def["evaluation_criteria"]["primary"]] + cohort_def["evaluation_criteria"]["additional"]},
                        f"{ref}: criterion is one the cohort permits", "X", "ADJ-CRITERION")
            refs2 = p.get("assessment_refs", [])
            for x in refs2:
                r.check(x in assess and assess[x]["payload"]["pre_consensus"] and assess[x]["sequence"] < ev["sequence"],
                        f"{ref}: assessment reference resolves, is pre-consensus, and precedes the adjudication", "X", "ADJ-ASSESS")
            # The adjudication binds its own charter. Reaching charter constraints
            # only through cited assessments meant an adjudication citing none
            # escaped every one of them.
            if charter is not None:
                cr = p.get("charter_ref")
                r.check(cr is not None
                        and (cr.get("artifact_id"), cr.get("version")) == (charter["artifact_id"], charter["version"]),
                        f"{ref}: adjudication binds the criterion's charter", "X", "ADJ-CHARTER")
                if cr:
                    defs.resolve(cr, f"{ref} adjudication charter")
            rp = (charter or {}).get("revision_protocol", {})
            method = p["resolution_process"]["method"]
            if charter is not None:
                allowed_all = set(charter["disagreement_pathway"]["method"].split()) | {"consensus"} | set(rp.get("authorized_methods", []))
                r.check(method in allowed_all,
                        f"{ref}: resolution method authorized by the charter", "X", "ADJ-METHOD")
                free = set(rp.get("assessment_free_methods", []))
                if method in free:
                    r.check("inter_adjudicator_agreement" not in p,
                            f"{ref}: an assessment-free resolution records no agreement statistic, "
                            f"since there are no assessments to compute one over", "X", "ADJ-AGREE")
                    decider = p.get("deciding_adjudicator_ref")
                    roles = {x["adjudicator_ref"]: x.get("role") for x in charter.get("roster", [])}
                    r.check(decider is not None and roles.get(decider) == rp.get("deciding_role"),
                            f"{ref}: assessment-free resolution decided by the charter's authorized role",
                            "X", "ADJ-DECIDER")
                else:
                    r.check(len(refs2) >= charter["assessment_protocol"]["min_independent_assessments"],
                            f"{ref}: charter minimum independent assessments satisfied", "X", "ADJ-MIN")
                actors = [assess.get(x, {}).get("payload", {}).get("adjudicator_ref") for x in refs2]
                need_independent = 0 if method in set(rp.get("assessment_free_methods", [])) \
                    else charter["assessment_protocol"]["min_independent_assessments"]
                r.check(len(set(refs2)) == len(refs2)
                        and len(set(a for a in actors if a)) >= need_independent,
                        f"{ref}: independent assessments come from distinct adjudicators, no assessment cited twice",
                        "X", "ADJ-INDEPENDENT")
            if "inter_adjudicator_agreement" in p:
                agree_exe = (charter or {}).get("agreement_statistic")
                agree_mod = bind_rule(agree_exe, f"{ref} agreement statistic") if agree_exe else None
                if agree_mod is None:
                    r.check(False, f"{ref}: charter declares no executable agreement statistic",
                            "X", "ADJ-AGREE")
                else:
                    payloads = [assess.get(x, {}).get("payload", {}).get("assessment", {}) for x in refs2]
                    agree = agree_mod.agreement(payloads) if payloads else None
                    r.check(agree is not None
                            and abs(agree - p["inter_adjudicator_agreement"]["value"]) < 1e-12,
                            f"{ref}: recorded agreement recomputes under the charter's declared statistic",
                            "X", "ADJ-AGREE")
            r.check(("conclusion" in p) == (p["conclusion_status"] == "determinate"),
                    f"{ref}: conclusion iff determinate", "X", "ADJ-CONCL")
            adj_events.setdefault(ref, []).append(ev)

    superseded_adj = set()
    active_adj = {}
    for ref, evs in adj_events.items():
        by_hash = {e["integrity"]["event_hash"]: e for e in evs}
        roots = [e for e in evs if "revises_event_hash" not in e["payload"]]
        r.check(len(roots) == 1, f"{ref}: adjudication lineage has exactly one root", "X", "ADJ-LINEAGE")
        revised = set()
        for e in evs:
            rv = e["payload"].get("revises_event_hash")
            if rv:
                r.check(rv in by_hash, f"{ref}: revision cites an adjudication in this chain", "X", "ADJ-REVREF")
                r.check(rv not in revised, f"{ref}: lineage is a chain, not a fork", "X", "ADJ-FORK")
                revised.add(rv)
                superseded_adj.add(rv)
        leaves = [e for e in evs if e["integrity"]["event_hash"] not in revised]
        r.check(len(leaves) == 1, f"{ref}: exactly one active adjudication", "X", "ADJ-ACTIVE")
        if leaves:
            active_adj[ref] = leaves[0]

    # ------------------------------------ maturation derived from dates, not labels
    r.section("maturation (derived from index date, risk window, and cutoff)")
    linked_status = {}
    for ch in case_chains:
        ref = ch[0]["chain_ref"]
        if ref not in linked_cases:
            continue
        statuses = [e for e in ch if e["event_type"] == "linkage_status_updated"]
        primary_id = (primary_criterion or {}).get("artifact_id")
        has_primary = any(cs["evaluation_criterion_ref"]["artifact_id"] == primary_id
                          for e in statuses for cs in e["payload"]["criterion_states"])
        r.check(bool(statuses) and has_primary,
                f"{ref}: a criterion status is recorded under the primary criterion, so maturity is knowable",
                "X", "OL-STATUS")
        if not statuses:
            continue
        for ev in statuses:
            for cs in ev["payload"]["criterion_states"]:
                win = dur_days(cs["risk_window"])
                idx = iso(index_when.get(ref, ""))
                cut = iso(ev["payload"]["data_availability_cutoff"])
                if idx and cut and win is not None:
                    derived = "mature" if (cut - idx).days >= win else "pending"
                    r.check(cs["maturation_state"] == derived,
                            f"{ref}: recorded maturation matches derivation from dates ({derived})", "X", "MAT-DERIVED")
        linked_status[ref] = statuses[-1]
    mature = {ref for ref, ev in linked_status.items()
              for cs in ev["payload"]["criterion_states"] if cs["maturation_state"] == "mature"}
    missing = [ref for ref in mature if ref not in active_adj]
    r.check(not missing, f"every mature linked case has an active adjudication ({len(mature) - len(missing)}/{len(mature)})",
            "X", "OL-ADJUDICATED")
    profile["mature cases adjudicated"] = not missing
    profile["status recorded for every linked case"] = all(ref in linked_status for ref in linked_cases)

    # -------------------------------------------- checkpoints, coverage, cadence
    r.section("checkpoints, coverage, cadence")
    cks = sorted(cev("checkpoint_committed"), key=lambda e: e["payload"]["checkpoint_epoch"])
    by_ref = {ch[0]["chain_ref"]: ch for ch in case_chains}
    log = []
    coverage_map = {ref: -1 for ref in by_ref}
    prev_ck_time = None
    max_int = dur_days((cohort_def or {}).get("checkpoint_policy", {}).get("max_interval", "P100D")) or 100
    for ck in cks:
        p = ck["payload"]
        log += [canon(o) for o in p["head_observations"]]
        r.check(mth(log).hex() == p["checkpoint_log_root"] and len(log) == p["checkpoint_log_size"],
                f"checkpoint {p['checkpoint_epoch']}: log root recomputes from appended observations", "C", "CKPT-ROOT")
        if "consistency_proof" in p:
            cp = p["consistency_proof"]
            r.check(verify_consistency(cp["previous_size"], cp["previous_root"], p["checkpoint_log_size"],
                                       p["checkpoint_log_root"], cp["path"]),
                    f"checkpoint {p['checkpoint_epoch']}: RFC 9162 consistency proof verifies", "C", "CKPT-CONSIST")
        anchored = ck["integrity"]["event_hash"] in verified_anchors
        for o in p["head_observations"]:
            ch = by_ref.get(o["chain_ref"], [])
            actual = [e for e in ch if e["sequence"] == o["head_sequence"]]
            r.check(bool(actual) and actual[0]["integrity"]["event_hash"] == o["head_hash"],
                    f"checkpoint {p['checkpoint_epoch']}: committed head for {o['chain_ref']} matches the exported chain",
                    "C", "CKPT-HEAD")
            if anchored and o["chain_ref"] in by_ref:
                coverage_map[o["chain_ref"]] = max(coverage_map.get(o["chain_ref"], -1), o["head_sequence"])
        observed = {o["chain_ref"] for o in p["head_observations"]}
        r.check(not (set(by_ref) - observed), f"checkpoint {p['checkpoint_epoch']}: coverage matches the declared policy",
                "X", "CKPT-COVER")
        if prev_ck_time is not None:
            gap = (iso(ck["occurred_at"]) - prev_ck_time).days
            r.check(gap <= max_int, f"checkpoint {p['checkpoint_epoch']}: interval within declared policy ({gap}d <= {max_int}d)",
                    "X", "CKPT-CADENCE")
        prev_ck_time = iso(ck["occurred_at"])
    r.check(all(v >= 0 for v in coverage_map.values()),
            "every case chain has at least one externally anchored witnessed head", "X", "CKPT-ANCHORED")
    for ref, seq in coverage_map.items():
        if ref in by_ref and seq < by_ref[ref][-1]["sequence"]:
            where = "no verified anchor covers this chain at all" if seq < 0 else f"events after sequence {seq}"
            r.attest(f"{ref}: {where} not covered by a verified anchor")
    profile["checkpoint coverage meets policy"] = bool(cks)

    if a.witness:
        w = json.load(open(a.witness))
        match = [c for c in cks if c["payload"]["checkpoint_epoch"] == w["epoch"]]
        r.check(bool(match) and match[0]["payload"]["checkpoint_log_root"] == w["root"]
                and match[0]["payload"]["checkpoint_log_size"] == w["size"],
                f"witnessed checkpoint epoch {w['epoch']} matches this export", "C", "CKPT-WITNESS")
    else:
        r.attest("No separately held witness supplied: rewrite detection is limited to the verified external-anchor coverage map; unanchored suffixes establish internal consistency only (ERRATA-v0.1 Erratum 1)")

    # ------------------------------------------ snapshots: recomputable, in force
    r.section("snapshots")
    snaps = {}
    for s in cev("analysis_snapshot_committed"):
        p, idx = s["payload"], cohort.index(s)
        r.check(p["cohort_chain_head_before_snapshot"] == (cohort[idx - 1]["integrity"]["event_hash"] if idx else None),
                "snapshot commits the preceding cohort head", "X", "SNAP-PREV")
        tuples = p.get("population_tuples", [])
        r.check(mth([canon(x) for x in tuples]).hex() == p["population_commitment"]["root"]
                and len(tuples) == p["population_commitment"]["tree_size"],
                "snapshot population root recomputes from its shipped tuples", "C", "SNAP-ROOT")
        r.check({t["chain_ref"] for t in tuples} == set(by_ref), "snapshot covers every track", "X", "SNAP-COVER")
        for t in tuples:
            ch = by_ref.get(t["chain_ref"], [])
            actual = [e for e in ch if e["sequence"] == t["case_chain_sequence"]]
            r.check(bool(actual) and actual[0]["integrity"]["event_hash"] == t["case_chain_head"],
                    f"snapshot tuple for {t['chain_ref']} binds a real head at its sequence", "C", "SNAP-HEAD")
        want = in_force_at(idx)
        got = {(x["artifact_id"], x["version"]) for x in p["definition_versions"]}
        r.check(got == want, "snapshot definition versions equal the reconstructed in-force set", "X", "SNAP-INFORCE")
        for dv in p["definition_versions"]:
            defs.resolve(dv, "snapshot definition version")
        snaps[s["integrity"]["event_hash"]] = s

    # ----------------------------------------- derived artifacts and lifecycle
    r.section("derived artifacts")
    derived = Resolver(r, a.derived, "derived artifact")
    derived_by_id = {obj["artifact_id"]: (fn, obj, dg) for fn, obj, dg in derived.objects}
    lifecycle = {}
    for e in cohort:
        p = e.get("payload", {})
        if e["event_type"] == "derived_artifact_registered":
            lifecycle[p["derived_artifact_id"]] = {"status": "active", "hash": p["derived_artifact_hash"],
                                                   "snapshot": p["analysis_snapshot_ref"],
                                                   "deps": p["depends_on_event_hashes"]}
        elif e["event_type"] in ("derived_artifact_superseded", "derived_artifact_invalidated"):
            ent = lifecycle.get(p["derived_artifact_id"])
            r.check(ent is not None, f"lifecycle event references a registered artifact ({p['derived_artifact_id']})",
                    "X", "DRV-LIFECYCLE")
            if ent:
                ent["status"] = "superseded" if e["event_type"].endswith("superseded") else "invalidated"

    def truncated_active_adjudication(ref, upto_seq):
        evs = [e for e in by_ref[ref] if e["event_type"] == "reference_standard_adjudicated" and e["sequence"] <= upto_seq]
        revised = {e["payload"].get("revises_event_hash") for e in evs if e["payload"].get("revises_event_hash")}
        leaves = [e for e in evs if e["integrity"]["event_hash"] not in revised]
        return leaves[-1] if leaves else None

    r.section("metric recomputation (loaded rules, snapshot-frozen evidence)")
    for aid, ent in lifecycle.items():
        hit = derived_by_id.get(aid)
        if not r.check(hit is not None, f"derived {aid}: registered artifact ships in the package", "X", "DRV-SHIPPED"):
            continue
        fn, obj, dg = hit
        r.check(dg == ent["hash"], f"derived {aid}: registered hash matches the shipped artifact", "C", "DRV-HASH")
        r.check("lifecycle" not in obj and "status" not in obj and "prespecification_label" not in obj,
                f"derived {aid}: no stored status or prespecification label", "S", "DRV-NOLABEL")
        r.check(ent["snapshot"] in snaps, f"derived {aid}: snapshot resolves", "X", "DRV-SNAP")
        eng = obj["recomputability"]["derivation_software_digest"]
        r.check(eng.get("locator") is not None
                and os.path.exists(os.path.join(ROOT, eng["locator"]))
                and eng["digest"]["digest"] == file_digest(os.path.join(ROOT, eng["locator"])),
                f"derived {aid}: derivation engine is located and its digest matches those bytes",
                "C", "DRV-ENGINE")
        stale = [x for x in ent["deps"] if x in superseded_adj]
        r.check(not (ent["status"] == "active" and stale),
                f"derived {aid}: no active artifact depends on a superseded adjudication", "X", "DRV-STALE")
        metric_def = defs.resolve(obj["metric_definition_ref"], f"derived {aid} metric")
        if not (metric_def and proj_mod and binary_mod and ent["snapshot"] in snaps):
            continue
        metric_mod = bind_rule(metric_def["formal_definition"]["executable"], f"derived {aid} metric rule")
        snap_tuples = {t["chain_ref"]: t["case_chain_sequence"]
                       for t in snaps[ent["snapshot"]]["payload"]["population_tuples"]}
        records = []
        for ref in sorted(linked_cases):
            traj = trajectories.get(ref)
            adj = truncated_active_adjudication(ref, snap_tuples.get(ref, -1))
            if not traj or adj is None:
                continue
            records.append({
                "case_ref": ref,
                "trajectory": traj,
                "conclusion_status": adj["payload"]["conclusion_status"],
                "conclusion": adj["payload"].get("conclusion"),
                "adjudication_hash": adj["integrity"]["event_hash"],
                "index_time": index_when.get(ref),
            })

        # Individual-level metrics are real subject-scoped derivations, not cohort
        # metrics with a different label. Bind the subject and longitudinal window
        # BEFORE recomputation so every downstream count is over the declared slice.
        declared_unit = obj.get("unit_of_analysis")
        individual_gov = None
        if declared_unit == "individual_clinician":
            subject = obj.get("subject_ref")
            individual_gov = defs.resolve(obj["governance_ref"], f"derived {aid} secondary-use governance") \
                if obj.get("governance_ref") else None
            ow = obj.get("observation_window") or {}
            start, end = iso(ow.get("start", "")), iso(ow.get("end", ""))
            all_subject_records = [rec for rec in records
                                   if rec["trajectory"].get("baseline_actor") == subject
                                   and rec["trajectory"].get("evaluation_actor") == subject]
            window_records = [rec for rec in all_subject_records
                              if start and end and rec.get("index_time")
                              and start <= iso(rec["index_time"]) <= end]
            eligible_hashes = {rec["adjudication_hash"] for rec in window_records}
            r.check(bool(subject) and bool(all_subject_records),
                    f"derived {aid}: subject_ref resolves to projected decisions by that clinician",
                    "X", "UOA-SUBJECT")
            r.check(set(obj["projection_set"]["input_event_hashes"]) <= eligible_hashes,
                    f"derived {aid}: committed metric inputs belong to the declared subject and observation window",
                    "X", "UOA-SUBJECT")
            if individual_gov is not None and start and end:
                span_s = (end - start).total_seconds()
                max_s = individual_gov.get("max_observation_window_days", -1) * 86400
                r.check(start <= end and 0 <= span_s <= max_s,
                        f"derived {aid}: observation window is ordered and within governance maximum "
                        f"({span_s/86400:.2f}d of {individual_gov.get('max_observation_window_days')}d, exact seconds arithmetic)",
                        "X", "UOA-WINDOW")
                timing = individual_gov.get("governance_timing")
                gh2 = artifact_content_hash({k: v for k, v in individual_gov.items() if k != "content_hash"})
                gov_anchor = verified_anchors.get(gh2)
                prospective_ok = bool(gov_anchor) and iso(gov_anchor) <= start
                r.check(timing == "prospective" and prospective_ok or timing == "retrospective",
                        f"derived {aid}: governance timing declared truthfully "
                        f"(declared {timing}; anchored before window start: {prospective_ok})",
                        "X", "UOA-TIMING")
            else:
                r.check(False, f"derived {aid}: individual metric has resolvable governance and observation window",
                        "X", "UOA-WINDOW")
            records = window_records

        align_exe = metric_def.get("alignment_relation")
        align_mod = bind_rule(align_exe, f"derived {aid} alignment relation") if align_exe else None
        if align_mod is not None and primary_criterion is not None:
            # Declared data is authoritative; the module constant must agree with it,
            # so an independent verifier never has to read the reference module.
            need = (align_exe or {}).get("parameters", {}).get("answer_space_requirement")
            r.check(need is not None and need == getattr(align_mod, "ANSWER_SPACE_REQUIREMENT", None),
                    f"derived {aid}: alignment relation's declared parameters match its realization",
                    "X", "RULE-PARAMS")
            have = primary_criterion.get("answer_space_semantics")
            r.check(need is None or need == have,
                    f"derived {aid}: alignment relation suits the criterion's answer-space semantics "
                    f"(relation requires {need}, criterion declares {have})", "X", "MET-ALIGN")
        if align_mod is None and metric_def["metric_name"] == "EAR":
            r.check(False, f"derived {aid}: EAR declares no executable alignment relation", "S", "MET-ALIGN")
            continue
        if align_mod is None:
            import types
            align_mod = types.SimpleNamespace(aligns=lambda e, a: e == a)
        n, d, used_hashes, excl = recompute_metric(records, binary_mod, metric_mod, align_mod)
        r.check(obj["numerator"] == n and obj["denominator"] == d,
                f"derived {aid}: {metric_def['metric_name']} recomputes against the snapshot as {n}/{d}", "X", "MET-RECOMPUTE")
        r.check(sorted(used_hashes) == obj["projection_set"]["input_event_hashes"],
                f"derived {aid}: committed input set equals the adjudication events the recomputation used", "X", "MET-INPUTS")
        v = obj["value"]
        r.check((d == 0 and v is None) or (d > 0 and abs(v - n / d) < 1e-12),
                f"derived {aid}: value consistent with the recomputed counts", "X", "MET-ARITH")
        if d > 0:
            est_exe = metric_def.get("aggregation_and_uncertainty", {}).get("estimator")
            est_mod = bind_rule(est_exe, f"derived {aid} estimator") if est_exe else None
            declared_method = metric_def.get("aggregation_and_uncertainty", {}).get("interval_method")
            est_params = (est_exe or {}).get("parameters", {})
            if est_mod is not None:
                r.check(est_params.get("interval_method") == getattr(est_mod, "INTERVAL_METHOD", None)
                        and est_params.get("level") == getattr(est_mod, "LEVEL", None)
                        and est_params.get("tolerance") == getattr(est_mod, "TOLERANCE", None),
                        f"derived {aid}: estimator's declared parameters match its realization",
                        "X", "RULE-PARAMS")
                r.check(declared_method == est_params.get("interval_method"),
                        f"derived {aid}: declared interval_method matches the executable estimator",
                        "X", "MET-ESTIMATOR")
            wi = est_mod.interval(n, d) if est_mod else wilson_interval(n, d)
            tol = est_params.get("tolerance", 1e-9)
            got = obj.get("interval")
            r.check(bool(got) and abs(got["lower"] - wi["lower"]) <= tol and abs(got["upper"] - wi["upper"]) <= tol
                    and got["method"] == wi["method"],
                    f"derived {aid}: declared Wilson interval recomputes", "X", "MET-INTERVAL")
        # ---- unit of analysis and secondary-use governance (Section 9.3) ----
        cohort_unit = (cohort_def or {}).get("unit_of_analysis")
        r.check(cohort_unit is not None,
                "the cohort declares the unit of analysis its metrics may be reported at",
                "S", "UOA-DECLARED")
        COARSENESS = {"system": 0, "site": 1, "cohort": 2, "care_team": 3, "individual_clinician": 4}
        r.check(declared_unit is not None and cohort_unit is not None
                and COARSENESS.get(declared_unit, 9) <= COARSENESS.get(cohort_unit, -1),
                f"derived {aid}: reported at a unit the cohort authorises "
                f"(reported {declared_unit}, cohort declares {cohort_unit})", "X", "UOA-MATCH")
        if declared_unit == "individual_clinician":
            gov = individual_gov
            r.check(gov is not None,
                    f"derived {aid}: individual-level derivation resolves a secondary-use governance artifact",
                    "X", "UOA-GOVERNANCE")
            if gov is not None:
                gh = artifact_content_hash({k: v for k, v in gov.items() if k != "content_hash"})
                at = verified_anchors.get(gh)
                cut = gov.get("prespecification_cutoff", {}).get("cutoff_time")
                r.check(bool(at) and bool(cut) and iso(at) < iso(cut),
                        f"derived {aid}: governance artifact anchored before its declared cutoff",
                        "X", "UOA-GOVERNANCE")
                r.check(obj["denominator"] >= gov["min_cell_size"],
                        f"derived {aid}: denominator {obj['denominator']} meets the governance "
                        f"minimum cell size {gov['min_cell_size']}", "X", "UOA-CELLSIZE")
                cm = obj.get("case_mix_disclosure") or {}
                r.check(bool(cm.get("covariates"))
                        and (cm.get("adjusted") is True or gov["case_mix_adjustment"]["required"] is False),
                        f"derived {aid}: case mix and adjustment status are disclosed as governance requires; "
                        f"adequacy of the adjustment is not mechanically established",
                        "X", "UOA-CASEMIX")
                hs = gov.get("high_stakes_safeguards") or {}
                if (gov.get("purpose_code") in {"credentialing", "employment", "litigation_support", "regulatory_oversight"}
                    or gov.get("decision_consequence") in {"remediation", "privileging", "credentialing", "employment", "litigation", "regulatory"}):
                    r.check(all(hs.get(k) is True for k in ("aggregate_metric_sole_basis_prohibited",
                                                           "case_level_review_required",
                                                           "subject_access_to_evidence",
                                                           "subject_notification_required",
                                                           "appeal_available")),
                            f"derived {aid}: high-stakes governance declares case review, subject notice/access, appeal, "
                            f"and prohibits aggregate-only adverse action",
                            "S", "UOA-HIGHSTAKES")

            # Balanced context is recomputed over the ASSIGNED subject population,
            # not the metric-eligible one. Metric eligibility filters (linked,
            # trajectory resolved, adjudicated) applied before the context made
            # the adjudication breakdown incapable of showing "not adjudicated",
            # defeating its anti-cherry-picking purpose (round 15).
            aref_ctx = (obj.get("reliance_context") or {}).get("assignment_ref")
            assign_art = defs.resolve(aref_ctx, f"derived {aid} responsibility assignments") if aref_ctx else None
            r.check(assign_art is not None and assign_art.get("artifact_kind") == "responsibility_assignments",
                    f"derived {aid}: individual metric resolves a prospective responsibility assignment artifact",
                    "X", "UOA-ASSIGNMENT")
            assigned = []
            if assign_art:
                assigned = [x for x in assign_art["assignments"]
                            if x["subject_ref"] == subject and start and end
                            and start <= iso(x["decision_time"]) <= end]
            assigned_refs = {x["case_ref"] for x in assigned}
            adj_by_ref = {}
            for ch2 in case_chains:
                ref2 = ch2[0]["chain_ref"]
                adjs2 = [e for e in ch2 if e["event_type"] == "reference_standard_adjudicated"]
                if adjs2:
                    revised = {e["payload"].get("revises_event_hash") for e in adjs2}
                    leaf = [e for e in adjs2 if e["integrity"]["event_hash"] not in revised]
                    if leaf:
                        adj_by_ref[ref2] = leaf[-1]["payload"]["conclusion_status"]
            link_bd, mat_bd = {}, {}
            adj_bd = {"determinate": 0, "indeterminate": 0, "not_adjudicated": 0}
            for x in assigned:
                stt = track_state.get(x["case_ref"], "untracked")
                link_bd[stt] = link_bd.get(stt, 0) + 1
                if x["case_ref"] in adj_by_ref:
                    mat_bd["mature"] = mat_bd.get("mature", 0) + 1
                    adj_bd[adj_by_ref[x["case_ref"]]] = adj_bd.get(adj_by_ref[x["case_ref"]], 0) + 1
                elif stt == "linked":
                    mat_bd["pending"] = mat_bd.get("pending", 0) + 1
                    adj_bd["not_adjudicated"] += 1
                else:
                    mat_bd["not_applicable"] = mat_bd.get("not_applicable", 0) + 1
                    adj_bd["not_adjudicated"] += 1
            def vbreak(which):
                out = {"correct": 0, "incorrect": 0, "excluded": 0}
                for rec in records:
                    if rec.get("conclusion_status") != "determinate":
                        out["excluded"] += 1; continue
                    val = binary_mod.classify(rec["trajectory"][which], rec.get("conclusion"))
                    b = binary_mod.binary(val)
                    if b == "correct": out["correct"] += 1
                    elif b == "incorrect": out["incorrect"] += 1
                    else: out["excluded"] += 1
                return out
            expected_context = {
                "subject_decision_instance_count": len(assigned),
                "assignment_ref": aref_ctx,
                "linkage_breakdown": dict(sorted(link_bd.items())),
                "maturation_breakdown": dict(sorted(mat_bd.items())),
                "adjudication_breakdown": dict(sorted(adj_bd.items())),
                "metric_eligible_count": len(records),
                "subject_case_count": len(records),
                "adjudication_status_breakdown": dict(sorted(Counter(rec.get("conclusion_status", "missing") for rec in records).items())),
                "commensurability_breakdown": {
                    "commensurable": sum(bool(rec["trajectory"].get("commensurable")) for rec in records),
                    "noncommensurable": sum(not bool(rec["trajectory"].get("commensurable")) for rec in records),
                },
                "baseline_validity_breakdown": vbreak("baseline"),
                "ai_validity_breakdown": vbreak("ai"),
                "evaluation_validity_breakdown": vbreak("evaluation"),
                "ai_system_breakdown": dict(sorted(Counter(rec["trajectory"].get("ai_system_ref", "UNKNOWN") for rec in records).items())),
                "exposure_class_breakdown": dict(sorted(Counter(rec["trajectory"].get("exposure_class", "UNKNOWN") for rec in records).items())),
                "index_period_breakdown": dict(sorted(Counter(x["decision_time"][:7] for x in assigned).items())),
            }
            got_ctx = obj.get("reliance_context") or {}
            for bd in ("linkage_breakdown", "maturation_breakdown", "adjudication_breakdown"):
                r.check(sum(got_ctx.get(bd, {}).values()) == got_ctx.get("subject_decision_instance_count", -1),
                        f"derived {aid}: {bd} sums exactly to the subject instance count", "X", "UOA-CONTEXT-RECONCILE")
            r.check(got_ctx.get("metric_eligible_count") == len(records)
                    and len(records) <= got_ctx.get("subject_decision_instance_count", -1),
                    f"derived {aid}: metric-eligible subset is derivable from the full subject population "
                    f"({len(records)} of {got_ctx.get('subject_decision_instance_count')})", "X", "UOA-CONTEXT-METRIC")
            r.check(set(x["case_ref"] for x in assigned) >= {rec["case_ref"] for rec in records} if assigned else False,
                    f"derived {aid}: every metric input is a prospectively assigned subject decision",
                    "X", "UOA-CONTEXT-POPULATION")
            r.check(obj.get("reliance_context") == expected_context,
                    f"derived {aid}: individual metric carries balanced subject context recomputed over the full bounded window",
                    "X", "UOA-CONTEXT")

        prohibited = ("standard_of_care_determination", "reasonable_use_determination",
                      "competence_determination", "negligence_determination",
                      "legal_authority_determination", "admissibility_determination",
                      "adverse_action_recommendation", "credentialing_action_recommendation",
                      "employment_action_recommendation")
        r.check(not any(k in obj for k in prohibited),
                f"derived {aid}: carries no determination of standard of care, reasonable use, competence, "
                f"negligence, legal authority, admissibility, or adverse action",
                "S", "UOA-NONORM")

        dis = obj["disclosures"]

        # Disclosure accounting is snapshot-frozen just like the metric itself.
        # Recompute track, maturation, adjudication, follow-up and blinding state
        # from events at or before each committed snapshot head.
        snap_states = {}
        snap_status = {}
        snap_linked = []
        for ref, upto in snap_tuples.items():
            state = "unattempted"
            for ev in by_ref.get(ref, []):
                if ev["sequence"] > upto:
                    break
                if ev["event_type"] == "linkage_attempted":
                    state = ev["payload"]["attempt_result"]
            snap_states[ref] = state
            if state == "linked":
                snap_linked.append(ref)
            sts = [ev for ev in by_ref.get(ref, [])
                   if ev["sequence"] <= upto and ev["event_type"] == "linkage_status_updated"]
            snap_status[ref] = sts[-1]["payload"] if sts else None

        primary_ref = (cohort_def or {}).get("evaluation_criteria", {}).get("primary", {})
        primary_id = primary_ref.get("artifact_id")
        snap_mature = []
        followup_counts = Counter()
        for ref in snap_linked:
            stp = snap_status.get(ref)
            if stp:
                followup_counts[stp.get("followup_state", "unknown")] += 1
                for cs in stp.get("criterion_states", []):
                    if cs.get("evaluation_criterion_ref", {}).get("artifact_id") == primary_id and cs.get("maturation_state") == "mature":
                        snap_mature.append(ref)
                        break

        snap_adj = {ref: truncated_active_adjudication(ref, snap_tuples.get(ref, -1)) for ref in snap_linked}
        exp_linked = len(snap_linked)
        exp_failed = sum(1 for state in snap_states.values()
                         if state in ("failed", "decision_record_missing", "outcome_record_missing"))
        exp_amb = sum(1 for state in snap_states.values() if state == "ambiguous")
        exp_mature = len(snap_mature)
        exp_pending = exp_linked - exp_mature
        det = sum(1 for ref in snap_linked if snap_adj.get(ref)
                  and snap_adj[ref]["payload"]["conclusion_status"] == "determinate")
        ind = sum(1 for ref in snap_linked if snap_adj.get(ref)
                  and snap_adj[ref]["payload"]["conclusion_status"] == "indeterminate")

        blinded_committed = 0
        excluded_cats = set((charter or {}).get("blinding_plan", {}).get("excluded_evidence_categories", []))
        for ref in snap_mature:
            upto = snap_tuples.get(ref, -1)
            ass = [ev for ev in by_ref[ref]
                   if ev["sequence"] <= upto and ev["event_type"] == "adjudicator_assessment_committed"]
            if ass and all((not ev["payload"]["blinding_breach"])
                           and excluded_cats <= set(ev["payload"]["blinding_actual"]) for ev in ass):
                blinded_committed += 1

        cnt = dis["completeness_accounting"]
        expected_followup = dict(sorted(followup_counts.items()))
        r.check(cnt["membership_committed_population"] == total_committed
                and cnt["tracked"] == len(snap_tuples)
                and cnt["linked"] == exp_linked and cnt["linkage_failed"] == exp_failed
                and cnt["linkage_ambiguous"] == exp_amb and cnt["pending_maturation"] == exp_pending
                and cnt["mature"] == exp_mature and cnt["concluded_determinate"] == det
                and cnt["conclusion_status_breakdown"] == {"determinate": det, "indeterminate": ind}
                and cnt["followup_state_breakdown"] == expected_followup,
                f"derived {aid}: every completeness disclosure recomputes from the snapshot-frozen population",
                "X", "MET-DISCLOSE")

        # `blinded_committed` is mechanically reconstructed from the committed
        # packet/assessment record. `blinded` is intentionally zero because
        # actual blinding remains an A-class attestation (6.11e).
        r.check(dis["blinding_breakdown"] == {
                    "blinded_committed": blinded_committed,
                    "blinded": 0,
                    "unblinded_or_breached": exp_mature - blinded_committed,
                },
                f"derived {aid}: blinding disclosure recomputes from committed assessment evidence",
                "X", "MET-BLIND")

        plan2 = defs.resolve(dis["plan_reference"]["analysis_plan_ref"], f"derived {aid} plan")
        primary_expected = bool(plan2 and primary_criterion
                                and plan2.get("primary_evaluation_criterion_ref", {}).get("content_hash", {}).get("digest")
                                == artifact_content_hash({k: v2 for k, v2 in primary_criterion.items() if k != "content_hash"}))
        validation_present = bool((primary_criterion or {}).get("clinical_reference_standard", {}).get("validation"))
        r.check(dis["verification_rule"] == "OL-ADJUDICATED"
                and dis["primary_evaluation_criterion"] == primary_expected
                and dis["criterion_validation_present"] == validation_present,
                f"derived {aid}: rule, primary-criterion, and criterion-validation disclosures derive from definitions",
                "X", "MET-DISCLOSE")
        r.check(dis["commensurability_exclusions"] == excl["commensurability"]
                and dis["binary_projection_exclusions"] == {
                    "indeterminate": excl["indeterminate"],
                    "partially_correct": excl["partially_correct"],
                    "not_classifiable": excl["not_classifiable"],
                },
                f"derived {aid}: exclusion disclosures match the recomputation", "X", "MET-EXCL")
        if plan2:
            ph = artifact_content_hash({k: v2 for k, v2 in plan2.items() if k != "content_hash"})
            at = verified_anchors.get(ph)
            cut = plan2.get("prespecification_cutoff", {}).get("cutoff_time")
            r.check(bool(at) and bool(cut) and iso(at) < iso(cut),
                    f"derived {aid}: plan derived as prespecified against its declared cutoff", "X", "MET-PRESPEC")
    profile["metrics recompute from snapshot"] = not any(rule == "MET-RECOMPUTE" for rule, _ in r.failures)
    profile["snapshot per published metric"] = all(ent["snapshot"] in snaps for ent in lifecycle.values())
    profile["derived artifacts resolve"] = all(aid in derived_by_id for aid in lifecycle)
    profile["definitions resolve"] = not defs.duplicates

    r.section("export")
    es = pkg.get("export_head_signature")
    if es:
        check_sig(es, cohort_head, cohort[-1]["occurred_at"], "export head signature", "export-head")

    print(f"\n{r.n} checks, {len(r.failures)} failures")
    for rule, label in r.failures:
        print(f"  FAILED [{rule}] {label}")

    print(f"\nPROFILE: {a.profile}")
    for k, v in profile.items():
        print(f"  {'PASS' if v else 'FAIL'}  {k}")
    conformant = all(profile.values()) and not r.failures
    print(f"\n{a.profile} CONFORMANT" if conformant else f"\nNOT {a.profile} CONFORMANT")

    print("\nNormative attestations required by CLAIMS-CLASSIFICATION")
    print("(requirements no verifier can establish; a conformance claim MUST NOT assert them):")
    for rid, text in load_attestations():
        print(f"  [A] {rid}  {text}")

    print("\nLimitations of THIS verification invocation (not normative attestations):")
    for x in r.attestations:
        print(f"  [-] {x}")
    for x in ["Recomputation called dses_derivation.recompute_metric, the SAME orchestration the "
              "generator called, over the same loaded rule modules and the same dses_core "
              "canonicalization. This establishes that the declared rules reproduce the registered "
              "counts; it does not establish agreement between two independently written "
              "implementations (claim 7.3c)",
              "RFC 3161 anchor profiles, if present, were not parsed and were not credited"]:
        print(f"  [-] {x}")

    sys.exit(0 if conformant else 1)


def load_attestations():
    """Read the A-class rows out of CLAIMS-CLASSIFICATION so the runtime list and
    the normative inventory cannot drift apart. Three different numbers appeared
    in the previous candidate precisely because they were maintained separately."""
    path = os.path.join(ROOT, "CLAIMS-CLASSIFICATION.md")
    out = []
    if not os.path.exists(path):
        return out
    for line in open(path):
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 5:
            continue
        rid, req, _rule, cls, _support = cells
        tokens = [t.strip() for t in re.split(r"[+/]", cls.replace("*", "")) if t.strip()]
        if re.match(r"^\d", rid) and "A" in tokens:
            out.append((rid, req))
    return out


def _walk_executables(obj, path=""):
    if isinstance(obj, dict):
        if "rule_id" in obj and "code_artifact_digest" in obj and "fixtures_ref" in obj:
            yield path, obj
            return
        for k, v in obj.items():
            yield from _walk_executables(v, f"{path}.{k}" if path else k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _walk_executables(v, f"{path}[{i}]")


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as exc:  # a hostile package must yield a verdict, not a stack trace
        rule = "PKG-MALFORMED"
        print(f"\n  FAILED [{rule}] package is structurally unprocessable: "
              f"{type(exc).__name__}: {exc}")
        print("\nNOT CONFORMANT")
        sys.exit(1)
