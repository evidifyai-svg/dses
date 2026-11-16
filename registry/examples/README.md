# Format examples

Nothing in this directory is a registry entry, and nothing here is counted.

`reference-self-run-0.2.0.json` is what `tools/make_transcript.py` writes. It
was produced by unpacking the published v0.2.0 archive into an empty directory
and running the reference verifier on the reference example package. It shows
the format. It is the reference implementation checking its own example, so it
establishes nothing about any outside implementation and could never be listed
as a conformance transcript for one.

To reproduce it, download the v0.2.0 archive from the GitHub release, confirm
its SHA-256 against `../archives.json`, unpack it, and run the command recorded
in the file's `command` field from the unpacked directory.
