#!/usr/bin/env bash
# ==============================================================================
# generate-docs.sh - Auto-generates interface specifications from source code
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

PYTHON_BIN="python3"
if [[ -f "${REPO_DIR}/.venv/bin/python3" ]]; then
  PYTHON_BIN="${REPO_DIR}/.venv/bin/python3"
elif [[ -f "${PARENT_DIR}/.venv/bin/python3" ]]; then
  PYTHON_BIN="${PARENT_DIR}/.venv/bin/python3"
fi

"$PYTHON_BIN" tools/generate_docs.py
