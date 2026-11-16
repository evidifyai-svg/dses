# Entry fields

Field values that `check_registry.py` enforces for
`implementations/<slug>/entry.json`.

| Field | Allowed values | Meaning |
|---|---|---|
| `status` | `published`, `withdrawn` | Only `published` entries are counted |
| `implementation.kind` | `emitter`, `adapter`, `verifier` | What was built |
| `implementation.independence` | `independent`, `reference-derived`, `reference` | `independent`: engineered and maintained outside Evidify without the reference emitter code. `reference-derived`: an outside team built on the reference code. `reference`: the Evidify reference implementation itself |
| `implementation.reference_code_reused` | `none`, `partial`, `full` | Must be `none` when independence is `independent` |
| `implementation.ai_assistance` | free text, required | How AI tools were used. Disclosure does not disqualify. An attempt with no accountable human engineer is not counted as independent |
| `deployment.status` | `none`, `planned`, `live` | `live` requires both record dates and an aggregate record count from real actors |
| `deployment.setting` | `reader-study`, `acceptance-test`, `production-logging`, or empty | The three deployment kinds named in `FOUNDING-IMPLEMENTERS.md` |
| `deployment.emitter` | `own`, `reference` | Whose emitter produced the deployment's records |
| `evidence_package.data_class` | `synthetic`, `deidentified`, `locally-reproducible` | No patient or confidential production data is public |
| `reports`, `transcripts` | lists of file names | Each must exist under `reports/` or `transcripts/` |

Every other field is required free text unless the deployment status is
`none`, in which case the remaining deployment fields may be empty.
