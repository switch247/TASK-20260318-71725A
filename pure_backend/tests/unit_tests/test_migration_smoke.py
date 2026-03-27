"""Validate startup bootstrap and migration chain from a clean database."""

import os
import subprocess
import sys
from pathlib import Path


def test_alembic_upgrade_and_app_startup_smoke(tmp_path) -> None:
    project_root = Path(__file__).resolve().parents[2]
    database_path = tmp_path / "migration_smoke.db"
    database_url = f"sqlite+pysqlite:///{database_path.as_posix()}"

    env = os.environ.copy()
    env["DATABASE_URL"] = database_url
    env["ENFORCE_HTTPS"] = "false"

    migration = subprocess.run(
        [sys.executable, "-c", "from alembic.config import main as alembic_main; alembic_main(argv=['upgrade','head'])"],
        cwd=project_root,
        env=env,
        capture_output=True,
        text=True,
    )
    assert migration.returncode == 0, migration.stderr

    smoke = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from fastapi.testclient import TestClient; "
                "from src.main import app; "
                "client=TestClient(app); "
                "response=client.get('/api/v1/health'); "
                "assert response.status_code == 200"
            ),
        ],
        cwd=project_root,
        env=env,
        capture_output=True,
        text=True,
    )
    assert smoke.returncode == 0, smoke.stderr

