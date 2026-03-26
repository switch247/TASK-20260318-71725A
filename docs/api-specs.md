# API Overview

Base path: `/api/v1`

## Health

- `GET /health`

## Identity and Access

- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/refresh`
- `POST /auth/logout`
- `POST /auth/password/reset`
- `GET /auth/me`

## Organizations

- `POST /organizations`
- `POST /organizations/join`

## Process Domain

- `POST /process/definitions`
- `POST /process/instances`
- `GET /process/tasks/pending`
- `POST /process/tasks/decision`
- `POST /process/reminders/dispatch`

## Operations Analysis and Export

- `POST /analytics/dashboard`
- `POST /analytics/reports`
- `POST /analytics/exports`
- `POST /analytics/exports/preview`
- `POST /operations/search`

## Data Governance

- `POST /governance/imports`
- `POST /governance/snapshots`
- `POST /governance/snapshots/rollback`
- `POST /governance/jobs/bootstrap`

## Security and Compliance

- `POST /security/attachments`
- `GET /security/attachments/{attachment_id}?business_number=<business-number>`
- `POST /security/audit/append`

## Auth and Org Headers

- `Authorization: Bearer <access-token>`
- `X-Organization-Id: <organization-id>` for organization-scoped endpoints

## OpenAPI Authorization Behavior

- The API now uses FastAPI's `HTTPBearer` security dependency.
- In Swagger UI (`/docs`), use **Authorize** and provide the token value.
- The UI automatically sends the `Authorization: Bearer <token>` header.
- For org-scoped APIs, also provide `X-Organization-Id` manually in the request headers.

## Error Envelope

All domain errors are normalized as:

```json
{ "code": 400, "message": "Validation failed", "details": {} }
```
