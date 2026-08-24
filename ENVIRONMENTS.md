# Verified environments

`requirements.txt` pins the three direct dependencies. It does **not** pin the
transitive closure, and this package does not ship hash-pinned lockfiles,
because wheel hashes are platform and interpreter specific and a single lockfile
would be false for most readers. What is recorded here instead is the exact
resolved set from each environment in which the full gate has been observed
green, so a reader who wants byte-level reproduction has a target and a reader
who gets a different resolution knows what changed.

Reproducibility of the DSES artifacts themselves does not depend on this: every
hash in the package is over RFC 8785 canonical bytes, and `scripts/check_jcs.py`
fails the build before anything else if the installed canonicalizer disagrees
with the ECMAScript number spellings. That check exists precisely because a
non-conforming canonicalizer in a review environment once produced a false
positive about artifact hashes that were, in fact, correct.

## Gate output for this candidate

This block is written by `scripts/check_environments.py --write` from the gate
log and checked against the log on every `run_all.sh` run (step 7). It is the
only place in this file that carries counts. The previous candidate shipped
hand-typed counts here that were four numbers behind the gate; a document that
records reproducibility must not itself be irreproducible.

<!-- gate-counts:begin -->
- RFC 8785 canonicalization self-test: 6/6 vectors
- release lint: 0 problems
- schema validation of shipped artifacts: 206 objects, 0 errors
- semantic-cryptographic verifier: 2205 checks, 0 failures, OL CONFORMANT
- adversarial suite: 158 cases, 158 rejected at the asserted rule, 0 not
- quickstart: 2 valid examples passed, 6 targeted mutations rejected
- vocabulary check: 833 schema terms, 0 findings
- release manifest: 105 entries
<!-- gate-counts:end -->

## Environment A: Linux container

- Linux x86_64, Python 3.12
- jcs 0.2.1, jsonschema 4.23.0, cryptography 43.0.1
- Last observed green: this candidate, on the tree the release archive was
  built from. Counts as in the block above.

## Environment B: macOS, independent hardware, PyPI install

- macOS arm64 (Apple silicon), Python 3.14, pip 26.1.2
- Direct: jcs 0.2.1, jsonschema 4.23.0, cryptography 43.0.1
- Transitive as resolved: attrs 26.1.0, cffi 2.1.1, jsonschema-specifications
  2025.9.1, pycparser 3.0, referencing 0.37.0, rpds-py 2026.6.3
- Last observed green: 0.2.0-rc10 (2026-08-23). Not yet re-run at this
  candidate. On 2026-08-24 the interpreter on that host no longer imported
  `jcs`, so `run_all.sh` failed at step 0 as designed; the record above is
  the last green run, not a current one.

Environment B is the environment that closes the pinned-dependency question:
a real PyPI install on hardware outside the authoring container, on a newer
interpreter than the one used to build the package, with a transitive set that
resolved differently and produced identical results. A record here that names
an older candidate than the one you are reading is a gap, and it is stated as
one rather than carried forward.

## What is still not established

An independently written implementation. Both environments run the same
reference code. See claim 7.3c.
