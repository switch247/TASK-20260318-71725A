# API Overview

Base path: `/api/v1`

## Auth

- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/refresh`
- `POST /auth/logout`
- `POST /auth/password/reset`
- `POST /auth/password/recovery/start`
- `POST /auth/password/recovery/confirm`
- `GET /auth/me`

## Organizations

- `POST /organizations`
- `POST /organizations/join`

## Process

- `POST /process/definitions`
- `POST /process/instances`
- `GET /process/tasks/pending`
- `POST /process/tasks/decision`
- `POST /process/reminders/dispatch`

## Analytics and Operations

- `POST /analytics/dashboard`
- `POST /analytics/reports`
- `POST /analytics/exports`
- `POST /analytics/exports/preview`
- `POST /operations/search`

## Governance

- `POST /governance/imports`
- `POST /governance/snapshots`
- `GET /governance/snapshots?domain=<name>&page=<n>&limit=<n>`
- `POST /governance/snapshots/rollback`
- `POST /governance/jobs/bootstrap`
- `POST /governance/jobs/execute`

## Security

- `POST /security/attachments`
- `GET /security/attachments/{attachment_id}?business_number=<business-number>`
- `POST /security/audit/append`

## Error Codes

- `400` validation failure
- `401` unauthorized
- `403` forbidden
- `404` not found
- `409` conflict
