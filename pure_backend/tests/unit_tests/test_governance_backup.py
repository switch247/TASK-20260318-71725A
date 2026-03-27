import os
import subprocess
from datetime import datetime, UTC

import pytest

from src.services.governance_service import GovernanceService


def test_physical_backup_fails_when_pg_dump_missing_and_stub_disallowed(monkeypatch, db_session, tmp_path):
    # Ensure explicit disabling of stub
    monkeypatch.setenv("ALLOW_GOVERNANCE_BACKUP_STUB", "false")
    # Use a postgres-style DATABASE_URL so code exercises the pg_dump branch
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost/testdb")
    # Simulate pg_dump missing by making subprocess.run raise
    def _bad_run(*args, **kwargs):
        raise subprocess.CalledProcessError(1, "pg_dump")

    monkeypatch.setattr(subprocess, "run", _bad_run)

    svc = GovernanceService(session=db_session)
    now = datetime.now(UTC)
    with pytest.raises(RuntimeError):
        svc._trigger_physical_backup("org-1", now)


def test_physical_backup_fails_closed_when_pg_dump_fails(monkeypatch, db_session, tmp_path):
    monkeypatch.setenv("ALLOW_GOVERNANCE_BACKUP_STUB", "true")
    # Use a postgres-style DATABASE_URL so code exercises the pg_dump branch
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost/testdb")

    def _bad_run(*args, **kwargs):
        raise subprocess.CalledProcessError(1, "pg_dump")

    monkeypatch.setattr(subprocess, "run", _bad_run)

    svc = GovernanceService(session=db_session)
    now = datetime.now(UTC)
    with pytest.raises(RuntimeError, match="pg_dump failed"):
        svc._trigger_physical_backup("org-1", now)
