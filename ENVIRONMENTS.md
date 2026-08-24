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

## Environment A: Linux container

- Linux x86_64, Python 3.12
- jcs 0.2.1, jsonschema 4.23.0, cryptography 43.0.1
- Full gate green, including 6/6 canonicalization vectors.

## Environment B: macOS, independent hardware, PyPI install

- macOS arm64 (Apple silicon), Python 3.14, pip 26.1.2
- Direct: jcs 0.2.1, jsonschema 4.23.0, cryptography 43.0.1
- Transitive as resolved: attrs 26.1.0, cffi 2.1.1, jsonschema-specifications
  2025.9.1, pycparser 3.0, referencing 0.37.0, rpds-py 2026.6.3
- Full gate green: 6/6 canonicalization vectors, release lint 0 problems,
  199 objects 0 errors, 2027 checks 0 failures, OL CONFORMANT, 113/113
  adversarial cases rejected at the asserted rule, 68/68 release-manifest
  hashes verified against the published archive digest.

Environment B is the environment that closes the pinned-dependency question:
a real PyPI install on hardware outside the authoring container, on a newer
interpreter than the one used to build the package, with a transitive set that
resolved differently and produced identical results.

## What is still not established

An independently written implementation. Both environments run the same
reference code. See claim 7.3c.
