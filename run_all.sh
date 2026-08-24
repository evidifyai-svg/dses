#!/usr/bin/env bash
# DSES v0.2.0-rc10 release gate.
#
# Verify the shipped bytes first. Regeneration happens only afterward in an
# isolated temporary copy, so a broken shipped artifact cannot be overwritten
# before it is tested.
set -euo pipefail
cd "$(dirname "$0")"
TRUST="examples/anchor-trust-store.json"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
LOG="$TMP/gate.log"

gate() {
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
echo "=== 5. external quickstart examples and targeted mutations ==="
python3 tests/run_quickstart.py

echo
echo "=== 6. regeneration check in a temporary tree, never over the release ==="
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
echo "=== 7. normative coherence: prose vocabulary agrees with the schemas ==="
python3 scripts/check_vocabulary.py
}

# Steps 0 through 7 are captured so that step 8 can check the environment
# record against what the gate actually produced, not against a number typed
# by hand. pipefail carries a failing step through the tee.
gate 2>&1 | tee "$LOG"

echo
echo "=== 8. environment record carries the counts this gate produced ==="
python3 scripts/check_environments.py "$LOG"

echo
echo "=== 9. shipped prose: legal-exposure and hygiene rules (release-tree profile) ==="
if command -v node >/dev/null 2>&1; then
  node scripts/check-language.mjs --config scripts/guard-spec.json --root . --ship none 2>&1 | grep -vE '^warn|^notice'
else
  echo "node not found: language guard skipped in this environment; CI runs it" >&2
  exit 1
fi

echo
echo "ALL GREEN (shipped artifacts verified before regeneration)"
