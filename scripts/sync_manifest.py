#!/usr/bin/env python3
"""Regenerate the working-tree RELEASE-MANIFEST.sha256.

The member list comes from make_release.members(), not from a second copy of the
allowlist here: two lists that must agree is the defect this specification keeps
finding elsewhere, and there is no reason to introduce one in its own tooling.

The published archive regenerates its manifest at build time. Without this, the
in-repo copy drifts, and a reader verifying from the repository sees mismatches
that a reader verifying from the ZIP does not. Release lint check L10 fails the
build whenever they diverge.
"""
import hashlib
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import make_release  # noqa: E402

paths = [p for p in make_release.members()
         if os.path.relpath(p, ROOT) != "RELEASE-MANIFEST.sha256"]
with open(os.path.join(ROOT, "RELEASE-MANIFEST.sha256"), "w") as out:
    for p in paths:
        rel = os.path.relpath(p, ROOT)
        d = hashlib.sha256(open(p, "rb").read()).hexdigest()
        out.write(f"{d}  {rel}\n")
print(f"release manifest: {len(paths)} entries")
