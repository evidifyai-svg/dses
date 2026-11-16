#!/usr/bin/env python3
"""Record a verification run as a registry transcript.

Runs the command given after `--`, captures its combined output and exit code
verbatim, and writes one JSON file naming the specification archive digest,
the digest of every subject file, and the environment. Standard library only.

The tool records. It does not judge the result, summarize the output, or
decide whether the run supports any claim. Whether a transcript may be listed
as a conformance transcript is decided against CONFORMANCE-POLICY.md.
"""
import argparse
import datetime
import hashlib
import json
import os
import platform
import re
import subprocess
import sys

FORMAT = "dses-registry-transcript/1"
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HEX64 = re.compile(r"^[0-9a-f]{64}$")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def pinned_packages(requirements):
    """Installed versions of the packages a requirements file names."""
    out = {}
    if not requirements or not os.path.exists(requirements):
        return out
    from importlib import metadata
    for line in open(requirements, encoding="utf8"):
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        name = re.split(r"[<>=!~;\[ ]", line, maxsplit=1)[0].strip()
        if not name:
            continue
        try:
            out[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            out[name] = "not installed"
    return out


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--" not in argv:
        sys.exit("usage: make_transcript.py [options] -- <verification command>")
    cut = argv.index("--")
    opts, command = argv[:cut], argv[cut + 1:]
    if not command:
        sys.exit("no verification command given after --")

    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--implementation", required=True, help="registry slug")
    ap.add_argument("--organization", required=True)
    ap.add_argument("--lead", required=True, help="accountable human technical lead")
    ap.add_argument("--dses-version", required=True)
    ap.add_argument("--claim-scope", required=True,
                    help='for example "DSES v0.2.0, outcome layer"')
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--archive", help="path to the specification archive verified against")
    g.add_argument("--archive-sha256", help="its SHA-256, if the file is not at hand")
    ap.add_argument("--subject", action="append", default=[],
                    help="file whose bytes were verified; repeat for each")
    ap.add_argument("--requirements", default=os.path.join(ROOT, "requirements.txt"),
                    help="requirements file whose installed versions are recorded")
    ap.add_argument("--env", action="append", default=[], metavar="KEY=VALUE",
                    help="extra environment fact, for non-Python runtimes; repeat")
    ap.add_argument("--limitations", default="",
                    help="what this run did not test, in the implementer's words")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(opts)

    if a.archive:
        archive = {"file": os.path.basename(a.archive), "sha256": sha256_file(a.archive)}
    else:
        if not HEX64.match(a.archive_sha256):
            sys.exit("--archive-sha256 must be 64 lowercase hex characters")
        archive = {"file": "", "sha256": a.archive_sha256}
    if not a.subject:
        sys.exit("at least one --subject is required: name the bytes that were verified")
    subjects = [{"file": os.path.basename(p), "sha256": sha256_file(p)} for p in a.subject]

    extra = {}
    for item in a.env:
        if "=" not in item:
            sys.exit(f"--env expects KEY=VALUE, got {item!r}")
        k, v = item.split("=", 1)
        extra[k] = v

    started = now()
    proc = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    finished = now()
    output = proc.stdout.decode("utf8", errors="replace")

    record = {
        "transcript_format": FORMAT,
        "implementation": a.implementation,
        "organization": a.organization,
        "accountable_lead": a.lead,
        "dses_version": a.dses_version,
        "claim_scope": a.claim_scope,
        "specification_archive": archive,
        "subjects": subjects,
        "command": command,
        "exit_code": proc.returncode,
        "started_utc": started,
        "finished_utc": finished,
        "output_sha256": hashlib.sha256(proc.stdout).hexdigest(),
        "output": output,
        "environment": {
            "os": platform.platform(),
            "machine": platform.machine(),
            "python": platform.python_version(),
            "packages": pinned_packages(a.requirements),
            "extra": extra,
        },
        "limitations": a.limitations,
    }
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", encoding="utf8") as f:
        json.dump(record, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"transcript written: {a.out}")
    print(f"command exit code: {proc.returncode} (recorded, not judged)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
