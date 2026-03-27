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

run_alembic_upgrade() {
  if command -v alembic >/dev/null 2>&1; then
    alembic upgrade head
    return
  fi
  python -c "from alembic.config import main as alembic_main; alembic_main(argv=['upgrade','head'])"
}

echo "[0/5] Alembic upgrade head"
run_alembic_upgrade

echo "[1/5] Ruff check"
run_ruff check .

echo "[2/5] Ruff format check"
run_ruff format --check .

echo "[3/5] Mypy"
run_mypy src

echo "[4/5] Pytest"
run_pytest

echo "All quality gates passed."
