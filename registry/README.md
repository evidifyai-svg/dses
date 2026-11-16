# DSES conformance and implementation registry

This directory is the registry that `CONFORMANCE-POLICY.md` and
`FOUNDING-IMPLEMENTERS.md` refer to. It holds the public evidence behind every
implementation, deployment, report, and transcript count in `SCORECARD.md`.

**Status, November 2026: empty.** No implementation entry, report, or
conformance transcript has been published. The templates and tools here exist
so that the first outside team is not waiting on Evidify for a format.

A registry entry is a record that evidence was published and where to find it.
It is not an endorsement, a badge, or a certification, and no certification
program exists.

## What lives here

| Path | Holds | Count it backs |
|---|---|---|
| `implementations/<slug>/entry.json` | One implementation: organization, accountable lead, workflow, version, independence, deployment status | Implementing organizations, independent implementations, real deployments |
| `reports/<slug>-<kind>-<yyyy-mm-dd>.md` | Implementation reports and interoperability reports | Implementation or interoperability reports |
| `transcripts/<slug>-<version>.json` | Verification transcripts that meet `CONFORMANCE-POLICY.md` | Conformance transcripts |
| `templates/` | Blank forms for all of the above | none |
| `tools/` | `make_transcript.py` and `check_registry.py` | none |
| `examples/` | Worked examples of the formats. Never counted | none |

Named expert reviews are not here. They are published in `docs/reviews/`.

## How to submit

No fee, no permission, and no contact with Evidify is needed to implement the
DSES specification or to prepare any of these files.

1. Copy `templates/entry.json` to `implementations/<slug>/entry.json` and fill
   it in. `<slug>` is a short lowercase name for the implementation.
2. Write the implementation report from
   `templates/IMPLEMENTATION-REPORT.md` and save it under `reports/`.
3. Run your verification and record it with `tools/make_transcript.py` (see
   below). A transcript goes under `transcripts/` only when it meets both
   requirements of `CONFORMANCE-POLICY.md`. A transcript that records failures
   belongs in the implementation report as an attachment or a link, where it is
   useful evidence, and it is not a conformance transcript.
4. Run `python3 registry/tools/check_registry.py`. It must exit 0.
5. Open a pull request. The same pull request changes the counts in
   `SCORECARD.md`; the checker fails if the counts and the registry disagree.

If the organization cannot be named until launch, follow the private route in
`FOUNDING-IMPLEMENTERS.md`. Nothing is counted until it is public.

## Recording a transcript

```sh
python3 registry/tools/make_transcript.py \
  --implementation my-emitter \
  --organization "Example Health" \
  --lead "A. Person" \
  --dses-version 0.2.0 \
  --archive dses-v0.2.0-publication.zip \
  --subject path/to/your/package.json \
  --claim-scope "DSES v0.2.0, outcome layer" \
  --out registry/transcripts/my-emitter-0.2.0.json \
  -- python3 scripts/dses_verify.py path/to/your/package.json --anchor-trust path/to/trust-store.json
```

Everything after `--` is the command you ran. The tool runs it, captures the
output and exit code verbatim, and records the specification archive digest,
the digest of each subject file, and the environment (OS, runtime, pinned
dependency versions). It does not judge the result and it does not edit the
output. A reader can rerun the same command against the same digests.

A transcript states that a named command produced a named output against named
bytes in a named environment. It does not establish that the records describe
what happened, that the deployment emits records for every in-scope decision,
or anything about clinical performance, fault, or legal position.

## What a maintainer checks before merging

- The entry names an organization and an accountable human lead.
- The public evidence package contains no patient data and no confidential
  production data.
- Labels are correct: schema-valid, compatible, and conformant are not used as
  synonyms, and any conformant claim is scoped to a version and a layer.
- The independence field is supported by the report (what code was reused,
  who wrote the emitter, how AI assistance was used).
- `check_registry.py` passes and the scorecard counts match.

A maintainer does not review the implementer's source code as a condition of
listing, and listing says nothing about its quality.

## Corrections and removal

An implementer may correct or withdraw an entry by pull request at any time.
A withdrawn entry is removed from the counts in the same pull request. Git
history keeps the record of what was listed and when.
