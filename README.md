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
pure_backend/src/
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

- API Service (dev / no TLS): `http://localhost:8000`
- API Service (TLS / enforced HTTPS): `https://localhost:8000`
- OpenAPI Docs (Swagger UI): `/docs` (use the same scheme as the API)
- ReDoc: `/redoc`
- Health Endpoint: `/api/v1/health`
- PostgreSQL (Docker): `localhost:5432`

## Test Directories

- Unit tests: `tests/unit_tests`
- API tests: `tests/API_tests`

## Verification Method

1. Service health check:

- If running locally and you need to simulate a TLS-terminating proxy, send the `x-forwarded-proto` header (the middleware checks this header):

```bash
curl -H "x-forwarded-proto: https" http://localhost:8000/api/v1/health
```

- If the service is bound with TLS (or in production behind TLS):

```bash
curl https://localhost:8000/api/v1/health --insecure
```

Expected response for both:

```json
{"status":"ok"}
```

Note: the application includes an HTTPS enforcement middleware that returns 400 for non-HTTPS `/api` requests unless the request is seen as HTTPS via `x-forwarded-proto` from a proxy. The repository also provides an `ENFORCE_HTTPS` and `TRUSTED_PROXY_HEADERS` environment flags in `pure_backend/.env.example` for configuration; the README documents the runtime behavior but does not change middleware logic.

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
