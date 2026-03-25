# Operations Runbook

## Environment Setup

1. Copy `.env.example` to `.env`.
2. Set secure values for `JWT_SECRET_KEY` and `ENCRYPTION_KEY`.
3. Start PostgreSQL and API through Docker compose.

## Start Services

```bash
docker compose up --build
```

This project uses Docker as the runtime baseline across environments.

## Database

- Alembic is configured in `alembic.ini` and `alembic/env.py`.
- Startup currently ensures schema exists with SQLAlchemy metadata create.
- Role-permission baseline is seeded at startup.
- Demo dataset seeding is available via:

```bash
docker compose exec -w /app app env PYTHONPATH=/app python scripts/seed_demo_data.py
```

## Quality Gates

Use the single command:

```bash
./run_tests.sh
```

This runs:

- Ruff lint
- Ruff format check
- Mypy strict typing
- Pytest with coverage

Current test scope includes:

- Auth, process, governance, analytics, security, and operations API tests
- Attachment upload boundary validation (`20MB` accepted, `20MB + 1 byte` rejected)
- Seed service verification for demo data population
- Tests are separated into `tests/unit_tests` and `tests/API_tests`
- HTTPS enforcement, workflow branch/parallel execution, and attachment business ownership checks
- SLA reminder dispatch API and no-duplicate reminder audit checks

Additional high-risk coverage includes:

- Same-organization, wrong-business attachment access denial
- Reminder dispatch permission boundary (`process:manage` required)
- Known KPI semantic mapping in dashboard response (`kpi_type`)

## Security Notes

- Keep production deployment behind HTTPS termination.
- Restrict who can access `.env` and logs.
- Rotate JWT and encryption secrets per policy.
- Do not store plaintext sensitive identifiers.

## Backup and Retention

- Daily backup and archive jobs can be bootstrapped via governance endpoint.
- Scheduler jobs are persisted with retry count and max retries (3).
