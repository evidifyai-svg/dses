#!/usr/bin/env python3
"""Build the public DSES v0.2.0-rc12 archive from an explicit allowlist.

The ZIP is deterministic for a fixed source tree: members are sorted and carry
one fixed timestamp. Build artifacts, review notes, local environments, VCS
state, and nested archives are never copied by discovery.
"""
from pathlib import Path
import hashlib
import re
import os
import sys
import zipfile

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = ROOT.parent / "dses-v0.2.0-rc12-publication.zip"
FILES = [
    "DSES-v0.1.md", "dses-v0.1.schema.json", "DSES-v0.2.md", "ERRATA-v0.1.md",
    "CLAIMS-CLASSIFICATION.md", "README.md", "IMPLEMENT.md",
    "IMPLEMENTATION-CHECKLIST.md", "FOUNDING-IMPLEMENTERS.md",
    "CONFORMANCE-POLICY.md", "SCORECARD.md", "ENVIRONMENTS.md",
    "RELIANCE-CONTEXT-EXAMPLE.md", "TERMINOLOGY.md", "CLAIM-LEDGER.md",
    "ERRATA-v0.2.md", "LICENSE-SPEC.md", "LICENSE-CODE.md",
    "requirements.txt", "run_all.sh",
]
DIRS = ["schemas", "artifacts", "examples", "fixtures", "quickstart", "rules", "scripts", "tests"]
SKIP_SUFFIX = {".pyc", ".pyo", ".zip"}
SKIP_DIRS = {"__pycache__", ".git", ".venv"}
STAMP = (2026, 8, 20, 0, 0, 0)


def members():
    out = []
    for name in FILES:
        p = ROOT / name
        if not p.is_file():
            raise SystemExit(f"missing release file: {name}")
        out.append(p)
    for dirname in DIRS:
        base = ROOT / dirname
        if not base.is_dir():
            raise SystemExit(f"missing release directory: {dirname}")
        for p in base.rglob("*"):
            if not p.is_file():
                continue
            rel = p.relative_to(ROOT)
            if any(part in SKIP_DIRS for part in rel.parts) or p.suffix in SKIP_SUFFIX:
                continue
            out.append(p)
    return sorted(set(out), key=lambda p: p.relative_to(ROOT).as_posix())


def zwrite(zf, rel, data, executable=False):
    zi = zipfile.ZipInfo(rel, STAMP)
    zi.compress_type = zipfile.ZIP_DEFLATED
    zi.create_system = 3
    mode = 0o755 if executable else 0o644
    zi.external_attr = (mode & 0xFFFF) << 16
    zf.writestr(zi, data)


def main():
    out = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DEFAULT_OUT
    # The output filename and the specification's Version line are two
    # statements of the same fact, and nothing used to check they agreed. This
    # built dses-v0.2.0-rc12-publication.zip from an rc11 tree once, silently,
    # and the resulting archive was one command away from being published under
    # a version it did not contain. If the filename names a version, it must be
    # the version in the tree.
    named = re.search(r"\d+\.\d+\.\d+(?:-rc\d+)?", out.name)
    if named:
        spec = (ROOT / "DSES-v0.2.md").read_text(encoding="utf8")
        line = re.search(r"^\*\*Version:\*\*\s*(\S+)", spec, re.M)
        actual = line.group(1) if line else None
        if actual and named.group(0) != actual:
            sys.exit(f"refusing to build: output path names {named.group(0)} but the "
                     f"specification Version line says {actual}; rename the output or "
                     f"bump the tree")
    items = members()
    manifest = []
    with zipfile.ZipFile(out, "w") as zf:
        for p in items:
            rel = p.relative_to(ROOT).as_posix()
            data = p.read_bytes()
            manifest.append(f"{hashlib.sha256(data).hexdigest()}  {rel}")
            executable = os.access(p, os.X_OK) or p.suffix == ".py" or rel == "run_all.sh"
            zwrite(zf, rel, data, executable)
        mdata = ("\n".join(manifest) + "\n").encode("utf-8")
        zwrite(zf, "RELEASE-MANIFEST.sha256", mdata)
    print(f"built {out}: {len(items) + 1} members")
    print(f"archive sha256 {hashlib.sha256(out.read_bytes()).hexdigest()}")

if __name__ == "__main__":
    main()
