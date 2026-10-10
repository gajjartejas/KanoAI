#!/usr/bin/env bash
# ==============================================================================
# KanoAI Test Runner
# Runs all Python unit tests for OCR, TTS, and launcher services.
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "${SCRIPT_DIR}/docs/index.html" ]; then
  REPO_ROOT="${SCRIPT_DIR}"
elif [ -f "${SCRIPT_DIR}/../docs/index.html" ]; then
  REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
else
  REPO_ROOT="${SCRIPT_DIR}"
fi

PYTHON_BIN=""
if [ -x "${REPO_ROOT}/.venv/bin/python3" ]; then
  PYTHON_BIN="${REPO_ROOT}/.venv/bin/python3"
elif [ -x "${REPO_ROOT}/.venv/bin/python" ]; then
  PYTHON_BIN="${REPO_ROOT}/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python3)"
else
  PYTHON_BIN="python"
fi

echo "================================================================="
echo "  🧪 Running KanoAI Test Suite (OCR, TTS, System Utilities)"
echo "================================================================="
echo "🐍 Python: ${PYTHON_BIN}"
echo "📁 Root:   ${REPO_ROOT}"
echo ""

cd "${REPO_ROOT}"
PYTHONPATH="${REPO_ROOT}/python:${REPO_ROOT}/scripts" "${PYTHON_BIN}" -m unittest discover -s python/tests -p "test_*.py" -v

echo ""
echo "================================================================="
echo "  ✓ All KanoAI Unit Tests Passed Successfully!"
echo "================================================================="
