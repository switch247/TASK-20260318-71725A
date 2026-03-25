#!/usr/bin/env bash
set -euo pipefail

USER_SCRIPTS_DIR="${APPDATA:-}/Python/Python311/Scripts"

run_ruff() {
  if command -v ruff >/dev/null 2>&1; then
    ruff "$@"
    return
  fi
  if [ -f "$USER_SCRIPTS_DIR/ruff.exe" ]; then
    "$USER_SCRIPTS_DIR/ruff.exe" "$@"
    return
  fi
  python -m ruff "$@"
}

run_mypy() {
  if command -v mypy >/dev/null 2>&1; then
    mypy "$@"
    return
  fi
  if [ -f "$USER_SCRIPTS_DIR/mypy.exe" ]; then
    "$USER_SCRIPTS_DIR/mypy.exe" "$@"
    return
  fi
  python -m mypy "$@"
}

run_pytest() {
  if command -v pytest >/dev/null 2>&1; then
    pytest "$@"
    return
  fi
  if [ -f "$USER_SCRIPTS_DIR/pytest.exe" ]; then
    "$USER_SCRIPTS_DIR/pytest.exe" "$@"
    return
  fi
  python -m pytest "$@"
}

echo "[1/4] Ruff check"
run_ruff check .

echo "[2/4] Ruff format check"
run_ruff format --check .

echo "[3/4] Mypy"
run_mypy src

echo "[4/4] Pytest"
run_pytest

echo "All quality gates passed."
