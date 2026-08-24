#!/usr/bin/env python3
"""Fail fast if the installed canonicalizer does not match key RFC 8785 / ECMAScript cases.

This catches a particularly dangerous failure mode for DSES: a package can be
internally self-consistent while all parties use the same non-JCS serializer.
The vectors below are deliberately chosen around JSON number spellings that
ordinary Python json serialization commonly gets wrong for JCS.
"""
import jcs

VECTORS = [
    ({"x": 1.0}, b'{"x":1}'),
    ({"x": -0.0}, b'{"x":0}'),
    ({"x": 1e-7}, b'{"x":1e-7}'),
    ({"x": 1e-6}, b'{"x":0.000001}'),
    ({"x": 1e20}, b'{"x":100000000000000000000}'),
    ({"b": 1, "a": 2}, b'{"a":2,"b":1}'),
]

for obj, expected in VECTORS:
    got = jcs.canonicalize(obj)
    if got != expected:
        raise SystemExit(f"RFC 8785 canonicalization self-test failed: {obj!r} -> {got!r}, expected {expected!r}")
print(f"RFC 8785 canonicalization self-test: {len(VECTORS)} vectors passed")
