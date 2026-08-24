# DSES sequence quickstart

These files are synthetic integration examples for the v0.1 sequence layer.
They are intentionally smaller than the v0.2 outcome-evidence package.

## Verify both flows

From the repository root, after installing `requirements.txt`:

```sh
bash quickstart/verify.sh
```

The command performs JSON Schema validation and quickstart-profile semantic
checks. It does not register a conformance claim.

## Copy the right flow

- `passive-exposure.json` is L1/I1. Emit availability at model completion,
  presentation at the user-interface boundary, and the final accountable
  decision. It intentionally includes no pre-AI state.
- `sealed-sequence.json` is L2/I2. Its disclosed synthetic payloads recompute to
  their `sha256:` references, and each event hash covers the RFC 8785 event
  preimage and predecessor. This establishes internal consistency of the sample
  export only.

The sample's `sha256:` payload references are binding content digests over
disclosed synthetic values. They are not hiding commitments: a low-entropy
answer could be guessed. Production concealment needs a nonce-backed hiding
commitment and controlled nonce disclosure.

The sealed sample has no separately held checkpoint, no external timestamp
anchor, and no deployed fail-closed release mechanism. Do not relabel it as I3,
historically immutable, or `DSES Conformant`.

The `python/` and `typescript/` directories show a single passive presentation
emitter small enough to move into an existing codebase. The Python example also
shows the pinned RFC 8785 commitment operation. The TypeScript example remains
I1 on purpose: ordinary `JSON.stringify` is not an RFC 8785 implementation.
