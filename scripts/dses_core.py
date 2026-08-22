"""DSES v0.2.0-rc3 cryptographic core.

One implementation of every primitive, shared by the generator, the verifier,
and the regression harness, so that no claim in the specification is verified
by code that differs from the code that produced the artifact.

Primitives:
  canon()                RFC 8785 JSON Canonicalization Scheme
  event_preimage_hash()  DSES event hash preimage (Section 3.1)
  artifact_content_hash()  Definition artifact content hash (Section 3.1)
  mth / inclusion / consistency   RFC 9162 sha-256 Merkle tree
  sign_dses / verify_dses         DSES-SIG-v1 signature profile (Section 3.6)
"""
import copy
import hashlib

import jcs
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric import ed25519


# ---------------------------------------------------------------- serialization

def canon(obj) -> bytes:
    return jcs.canonicalize(obj)


def h(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def event_preimage_hash(ev: dict) -> str:
    """Section 3.1: RFC 8785 canonical form of the event with
    integrity.event_hash, signatures, and payload removed."""
    pre = copy.deepcopy(ev)
    pre.pop("payload", None)
    pre.pop("signatures", None)
    pre["integrity"].pop("event_hash", None)
    return h(canon(pre))


def artifact_content_hash(artifact: dict) -> str:
    """Section 3.1: canonical form with content_hash removed. Anchor evidence is
    NOT part of the artifact (Section 3.5), so improving timing evidence never
    changes artifact identity."""
    a = copy.deepcopy(artifact)
    a.pop("content_hash", None)
    return h(canon(a))


# ------------------------------------------------------------------ RFC 9162

def mth_leaf(entry: bytes) -> bytes:
    return hashlib.sha256(b"\x00" + entry).digest()


def mth_node(left: bytes, right: bytes) -> bytes:
    return hashlib.sha256(b"\x01" + left + right).digest()


def _split(n: int) -> int:
    k = 1
    while k * 2 < n:
        k *= 2
    return k


def mth(entries) -> bytes:
    n = len(entries)
    if n == 0:
        return hashlib.sha256(b"").digest()
    if n == 1:
        return mth_leaf(entries[0])
    k = _split(n)
    return mth_node(mth(entries[:k]), mth(entries[k:]))


def inclusion_path(m: int, entries):
    n = len(entries)
    if n == 1:
        return []
    k = _split(n)
    if m < k:
        return inclusion_path(m, entries[:k]) + [mth(entries[k:])]
    return inclusion_path(m - k, entries[k:]) + [mth(entries[:k])]


def verify_inclusion(leaf_entry: bytes, index: int, tree_size: int, path, root_hex: str) -> bool:
    """RFC 9162 Section 2.1.3.2."""
    if index >= tree_size:
        return False
    fn, sn = index, tree_size - 1
    r = mth_leaf(leaf_entry)
    for p_hex in path:
        p = bytes.fromhex(p_hex)
        if sn == 0:
            return False
        if fn % 2 == 1 or fn == sn:
            r = mth_node(p, r)
            while fn % 2 == 0 and fn != 0:
                fn //= 2
                sn //= 2
        else:
            r = mth_node(r, p)
        fn //= 2
        sn //= 2
    return sn == 0 and r.hex() == root_hex


def consistency_path(m: int, entries):
    """RFC 9162 Section 2.1.4: proof that the tree of size len(entries)
    is an append-only extension of the tree of its first m entries."""
    return _subproof(m, entries, True)


def _subproof(m: int, entries, b: bool):
    n = len(entries)
    if m == n:
        return [] if b else [mth(entries)]
    k = _split(n)
    if m <= k:
        return _subproof(m, entries[:k], b) + [mth(entries[k:])]
    return _subproof(m - k, entries[k:], False) + [mth(entries[:k])]


def verify_consistency(old_size: int, old_root_hex: str, new_size: int, new_root_hex: str, path) -> bool:
    """RFC 9162 Section 2.1.4.2 verification algorithm, verbatim."""
    if old_size < 1 or old_size > new_size:
        return False
    if old_size == new_size:
        return not path and old_root_hex == new_root_hex
    if not path:
        return False
    p = [bytes.fromhex(x) for x in path]
    if old_size & (old_size - 1) == 0:  # exact power of two: prepend first_hash
        p = [bytes.fromhex(old_root_hex)] + p
    fn, sn = old_size - 1, new_size - 1
    while fn & 1:
        fn >>= 1
        sn >>= 1
    fr = sr = p[0]
    for c in p[1:]:
        if sn == 0:
            return False
        if fn & 1 or fn == sn:
            fr = mth_node(c, fr)
            sr = mth_node(c, sr)
            while fn != 0 and not (fn & 1):
                fn >>= 1
                sn >>= 1
        else:
            sr = mth_node(sr, c)
        fn >>= 1
        sn >>= 1
    return sn == 0 and fr.hex() == old_root_hex and sr.hex() == new_root_hex


# ------------------------------------------------------- DSES-SIG-v1 profile

SIG_PREFIX = b"DSES-SIG-v1"


def signing_input(context_label: str, target_hash_hex: str) -> bytes:
    """Section 3.6. Domain-separated, unambiguous, and independent of JSON
    layout: the signature covers exactly one named hash under one named context.
    Length prefixes prevent concatenation ambiguity between fields."""
    ctx = context_label.encode()
    tgt = target_hash_hex.encode()
    return (
        SIG_PREFIX + b"\x00"
        + len(ctx).to_bytes(2, "big") + ctx
        + len(tgt).to_bytes(2, "big") + tgt
    )


def sign_dses(private_key, key_ref: str, context_label: str, target_hash_hex: str) -> dict:
    sig = private_key.sign(signing_input(context_label, target_hash_hex))
    return {
        "profile": "DSES-SIG-v1",
        "alg": "ed25519",
        "key_ref": key_ref,
        "context_label": context_label,
        "target_hash": target_hash_hex,
        "value": sig.hex(),
    }


def verify_dses(sig_obj: dict, public_key_hex: str) -> bool:
    try:
        if sig_obj.get("profile") != "DSES-SIG-v1" or sig_obj.get("alg") != "ed25519":
            return False
        pk = ed25519.Ed25519PublicKey.from_public_bytes(bytes.fromhex(public_key_hex))
        pk.verify(
            bytes.fromhex(sig_obj["value"]),
            signing_input(sig_obj["context_label"], sig_obj["target_hash"]),
        )
        return True
    except (InvalidSignature, ValueError, KeyError):
        return False


# ------------------------------------------------- anchor receipts (DSES-ANCHOR-v1)

def anchor_receipt_body(artifact_hash: str, anchor_time: str, tsa_identity: str) -> dict:
    return {"artifact_hash": artifact_hash, "anchor_time": anchor_time, "tsa_identity": tsa_identity}


def anchor_receipt_target(body: dict) -> str:
    """The hash an anchor authority signs. Binds artifact, time, and authority
    together so a receipt cannot be replayed onto another artifact or time."""
    return h(canon(body))


# ------------------------------------------------ estimator primitive

def wilson_interval(n: int, d: int, level: float = 0.95):
    """Wilson score interval; z fixed for the two supported levels."""
    if d == 0:
        return None
    z = {0.95: 1.959963984540054, 0.99: 2.5758293035489004}[level]
    p = n / d
    denom = 1 + z * z / d
    center = (p + z * z / (2 * d)) / denom
    half = (z / denom) * ((p * (1 - p) / d + z * z / (4 * d * d)) ** 0.5)
    return {"lower": max(0.0, center - half), "upper": min(1.0, center + half), "level": level, "method": "Wilson"}


def file_digest(path: str) -> str:
    with open(path, "rb") as f:
        return h(f.read())
