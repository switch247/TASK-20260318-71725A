# Operations Runbook

Run from project directory (all commands run via Docker):

```bash
cd pure_backend
cp .env.example .env
docker compose run --rm app python -c "from alembic.config import main; main(argv=['upgrade','head'])"
docker compose up --build
```

Quality checks (run inside container):

```bash
cd pure_backend
docker compose run --rm app bash -lc "./run_tests.sh"
```

Key maintenance endpoints:

- `/api/v1/process/reminders/dispatch`
- `/api/v1/governance/jobs/bootstrap`
- `/api/v1/governance/jobs/execute`

Operational notes:

- Daily backup jobs generate organization-scoped backup artifacts and record metadata snapshots for traceability.
- Archive jobs enforce 30-day retention by archiving eligible process records and storing archive metadata snapshots.
- For production, wire these job outputs to hardened platform backup storage and restore automation.
 
Migration & backup test notes:

- **Audit immutability:** An Alembic migration has been added to enforce append-only behavior for audit tables at the DB level for Postgres. See `alembic/versions/0004_enforce_log_immutability_postgres.py` for details. Apply migrations with:

```bash
docker compose run --rm app python -c "from alembic.config import main; main(argv=['upgrade','head'])"
```

- **Test-friendly backups:** Tests and CI may not have `pg_dump` available. To allow deterministic test runs we added an explicit opt-in env var `ALLOW_GOVERNANCE_BACKUP_STUB=true` for test environments. In production do not set this flag — the governance backup job will fail closed if `pg_dump` is unavailable.

