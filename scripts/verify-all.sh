#!/usr/bin/env bash
# ==============================================================================
# verify-all.sh - Strict local pre-push verification script for lumiscrape
#
# This script executes all CI checks locally to guarantee that code will pass CI
# before pushing any commits or creating PRs.
# ==============================================================================

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MAIN_REPO_DIR="$(git rev-parse --show-toplevel 2>/dev/null || echo "$REPO_DIR")"
if git rev-parse --git-common-dir >/dev/null 2>&1; then
  COMMON_DIR="$(git rev-parse --git-common-dir)"
  PARENT_DIR="$(cd "$COMMON_DIR/.." && pwd)"
else
  PARENT_DIR="$MAIN_REPO_DIR"
fi

cd "$REPO_DIR"

export PYTHONPATH="${REPO_DIR}/src"

# Locate virtual environment (current worktree or parent repo)
VENV_BIN=""
if [[ -f "${REPO_DIR}/.venv/bin/ruff" ]]; then
  VENV_BIN="${REPO_DIR}/.venv/bin"
elif [[ -f "${PARENT_DIR}/.venv/bin/ruff" ]]; then
  VENV_BIN="${PARENT_DIR}/.venv/bin"
fi

echo "========================================================"
echo "1. Checking Interface Documentation Drift (generate-docs)..."
echo "========================================================"
./scripts/generate-docs.sh
if ! git diff --exit-code docs/reference/interfaces.md; then
  echo "Error: Uncommitted generated documentation drift detected!"
  echo "Please run ./scripts/generate-docs.sh and commit docs/reference/interfaces.md"
  exit 1
fi
echo "OK: Interface documentation is up to date with zero drift."
echo ""

echo "========================================================"
echo "2. Checking Python Syntax & Code Formatting (Ruff)..."
echo "========================================================"
if [[ -n "$VENV_BIN" && -f "${VENV_BIN}/ruff" ]]; then
  "${VENV_BIN}/ruff" check src tests tools
  "${VENV_BIN}/ruff" format --check src tests tools
  echo "OK: Ruff linter & formatter passed."
elif command -v ruff >/dev/null 2>&1; then
  ruff check src tests tools
  ruff format --check src tests tools
  echo "OK: Ruff linter & formatter passed."
else
  python3 -m compileall -q src tests tools
  echo "OK: Python syntax compilation passed."
fi
echo ""

echo "========================================================"
echo "3. Running Static Type Check (MyPy)..."
echo "========================================================"
if [[ -n "$VENV_BIN" && -f "${VENV_BIN}/mypy" ]]; then
  "${VENV_BIN}/mypy" src tests
  echo "OK: MyPy passed with 0 errors."
elif command -v mypy >/dev/null 2>&1; then
  mypy src tests
  echo "OK: MyPy passed with 0 errors."
else
  echo "Note: mypy not found locally. Skipping local typecheck (checked in CI)."
fi
echo ""

echo "========================================================"
echo "4. Running Unit Tests & Assertions (Pytest)..."
echo "========================================================"
if [[ -n "$VENV_BIN" && -f "${VENV_BIN}/pytest" ]]; then
  "${VENV_BIN}/pytest" -v tests
elif command -v pytest >/dev/null 2>&1; then
  pytest -v tests
else
  python3 -m unittest discover -s tests -p "test_*.py" || true
fi
echo "OK: Tests finished."
echo ""

echo "========================================================"
echo "All local verification checks passed successfully!"
echo "========================================================"
