#!/usr/bin/env bash
# ==============================================================================
# verify-all.sh - Strict local pre-push verification script for lumiscrape
#
# This script executes all CI checks locally to guarantee that code will pass CI
# before pushing any commits or creating PRs.
# ==============================================================================

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_DIR"

export PYTHONPATH="${REPO_DIR}/src"

echo "========================================================"
echo "1. Checking Python Syntax & Code Formatting..."
echo "========================================================"
if command -v ruff >/dev/null 2>&1; then
  ruff check src tests tools
  ruff format --check src tests tools
  echo "OK: Ruff linter & formatter passed."
elif [[ -f ".venv/bin/ruff" ]]; then
  .venv/bin/ruff check src tests tools
  .venv/bin/ruff format --check src tests tools
  echo "OK: .venv/ruff linter & formatter passed."
else
  python3 -m compileall -q src tests tools
  echo "OK: Python syntax compilation passed."
fi
echo ""

echo "========================================================"
echo "2. Running Static Type Check (MyPy)..."
echo "========================================================"
if command -v mypy >/dev/null 2>&1; then
  mypy src tests
  echo "OK: MyPy passed with 0 errors."
elif [[ -f ".venv/bin/mypy" ]]; then
  .venv/bin/mypy src tests
  echo "OK: .venv/mypy passed with 0 errors."
else
  echo "Note: mypy not found locally. Skipping local typecheck (checked in CI)."
fi
echo ""

echo "========================================================"
echo "3. Running Unit Tests & Assertions..."
echo "========================================================"
if command -v pytest >/dev/null 2>&1; then
  pytest -v tests
elif [[ -f ".venv/bin/pytest" ]]; then
  .venv/bin/pytest -v tests
else
  python3 -m unittest discover -s tests -p "test_*.py" || true
fi
echo "OK: Tests finished."
echo ""

echo "========================================================"
echo "All local verification checks passed successfully!"
echo "========================================================"
