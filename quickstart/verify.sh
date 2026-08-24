#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON_BIN="${DSES_PYTHON:-python3}"
if [[ -x "$ROOT/.venv/bin/python" ]]; then
  PYTHON_BIN="$ROOT/.venv/bin/python"
fi
"$PYTHON_BIN" "$ROOT/scripts/verify_sequence.py" \
  "$ROOT/quickstart/passive-exposure.json" \
  "$ROOT/quickstart/sealed-sequence.json"
