#!/usr/bin/env python3
"""Build the public DSES v0.2.0-rc8 archive from an explicit allowlist.

The ZIP is deterministic for a fixed source tree: members are sorted and carry
one fixed timestamp. Build artifacts, review notes, local environments, VCS
state, and nested archives are never copied by discovery.
"""
from pathlib import Path
import hashlib
import os
import sys
import zipfile

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = ROOT.parent / "dses-v0.2.0-rc8-publication.zip"
FILES = [
    "DSES-v0.2.md", "ERRATA-v0.1.md", "CLAIMS-CLASSIFICATION.md", "README.md", "ENVIRONMENTS.md", "RELIANCE-CONTEXT-EXAMPLE.md",
    "LICENSE-SPEC.md", "LICENSE-CODE.md", "requirements.txt", "run_all.sh",
]
DIRS = ["schemas", "artifacts", "examples", "fixtures", "rules", "scripts", "tests"]
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
