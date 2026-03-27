# Operations Runbook

Run from project directory:

```bash
cd pure_backend
cp .env.example .env
alembic upgrade head
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

- Backup/archive jobs are logical governance snapshots in this offline project profile (dry-run summaries), not physical database backup/retention tooling.
- Physical backup/restore orchestration should be implemented through deployment platform automation (for example managed database snapshots and object-storage archives).

