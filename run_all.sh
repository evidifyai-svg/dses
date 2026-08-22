#!/usr/bin/env bash
# DSES v0.2.0-rc8 release gate.
#
# Verify the shipped bytes first. Regeneration happens only afterward in an
# isolated temporary copy, so a broken shipped artifact cannot be overwritten
# before it is tested.
set -euo pipefail
cd "$(dirname "$0")"
TRUST="examples/anchor-trust-store.json"

echo "=== 0. RFC 8785 canonicalization self-test ==="
python3 scripts/check_jcs.py

echo
python3 scripts/sync_manifest.py >/dev/null

echo "=== 1. release lint: specification/claims/verifier/fixtures agree ==="
python3 scripts/release_lint.py

echo
echo "=== 2. schema validation of SHIPPED artifacts (nothing modified) ==="
python3 scripts/validate_package.py

echo
echo "=== 3. semantic-cryptographic verifier of SHIPPED artifacts ==="
python3 scripts/dses_verify.py --anchor-trust "$TRUST" --quiet

echo
echo "=== 4. adversarial suite against SHIPPED artifacts ==="
python3 tests/run_regression.py

echo
echo "=== 5. regeneration check in a temporary tree, never over the release ==="
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
python3 - "$PWD" "$TMP/pkg" <<'PY'
import os, shutil, sys
src, dst = sys.argv[1], sys.argv[2]
ignore = shutil.ignore_patterns('.venv', '.git', '__pycache__', '*.pyc', '*.pyo', '*.zip')
shutil.copytree(src, dst, ignore=ignore)
PY
rm -rf "$TMP/pkg/examples/derived" "$TMP/pkg/examples/decision-sequences" "$TMP/pkg/artifacts"
mkdir -p "$TMP/pkg/examples/derived" "$TMP/pkg/examples/decision-sequences" "$TMP/pkg/artifacts"
(
  cd "$TMP/pkg"
  python3 scripts/generate_example.py >/dev/null
  python3 scripts/validate_package.py
  python3 scripts/dses_verify.py --anchor-trust examples/anchor-trust-store.json --quiet | tail -3
)

echo
echo "ALL GREEN (shipped artifacts verified before regeneration)"
