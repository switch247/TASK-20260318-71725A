# Operations Runbook

Run from project directory:

```bash
cd pure_backend
cp .env.example .env
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
