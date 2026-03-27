# Operations Runbook

Run from project directory:

```bash
cd pure_backend
cp .env.example .env
python -m alembic upgrade head
docker compose up --build
```

Quality checks:

```bash
./run_tests.sh
```

Key maintenance endpoints:

- `/api/v1/process/reminders/dispatch`
- `/api/v1/governance/jobs/bootstrap`
- `/api/v1/governance/jobs/execute`

Operational notes:

- Daily backup jobs generate organization-scoped backup artifacts and record metadata snapshots for traceability.
- Archive jobs enforce 30-day retention by archiving eligible process records and storing archive metadata snapshots.
- For production, wire these job outputs to hardened platform backup storage and restore automation.
