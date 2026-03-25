# Medical Operations and Process Governance Middle Platform API Service

Enterprise-grade FastAPI backend for hospital operations governance,
workflow approvals, analytics, export controls, data governance,
and compliance.

## Highlights

- FastAPI + SQLAlchemy + PostgreSQL
- JWT access/refresh authentication with refresh revocation
- Organization-level data isolation and RBAC
- Workflow engine with SLA and idempotency controls
- Sensitive field encryption and response desensitization
- Immutable audit trail and operation logs
- Dockerized deployment/runtime

## Project Structure

```
src/
  api/
  core/
  db/
  models/
  repositories/
  schemas/
  services/
  jobs/
tests/
config/
scripts/
```

## Quick Start

All commands in this README must be run from `pure_backend/`.

1. Copy environment template:

```bash
cp .env.example .env
```

2. Start services:

```bash
docker compose up --build
```

3. Open API docs:

- `http://localhost:8000/docs`

## Start Command (How to Run)

Docker-only runtime:

```bash
cd pure_backend
cp .env.example .env
docker compose up --build
```

## Service Address (Services List)

- API Service: `http://localhost:8000`
- OpenAPI Docs (Swagger UI): `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Health Endpoint: `http://localhost:8000/api/v1/health`
- PostgreSQL (Docker): `localhost:5432`

## Test Directories

- Unit tests: `tests/unit_tests`
- API tests: `tests/API_tests`

## Verification Method

1. Service health check:

```bash
curl http://localhost:8000/api/v1/health
```

Expected response:

```json
{"status":"ok"}
```

2. Run all quality gates and tests:

```bash
cd pure_backend
./run_tests.sh
```

3. Validate OpenAPI auth flow:

- Open `http://localhost:8000/docs`
- Click **Authorize** and paste JWT token
- Call a protected endpoint with `X-Organization-Id` set
- Confirm request includes `Authorization: Bearer <token>`


## Quality Gates

```bash
cd pure_backend
docker compose run --rm app ruff check .
docker compose run --rm app ruff format --check .
docker compose run --rm app mypy src
docker compose run --rm app pytest
./run_tests.sh
```

## Documentation

- Architecture and domain design: `docs/design.md`
- API reference: `docs/api.md`
- Architecture notes: `docs/architecture.md`
- Operations runbook: `docs/operations.md`
- Security and compliance controls: `docs/security.md`
- Role and permission matrix: `docs/roles-and-permissions.md`
- API docs: OpenAPI via `/docs`

## Coverage Highlights

- Workflow branching, parallel, and joint-sign task execution coverage
- SLA reminder dispatch and duplicate-prevention coverage
- HTTPS enforcement middleware coverage
- Attachment business-context ownership (IDOR-focused) coverage
- Export whitelist + role-based desensitization preview coverage
