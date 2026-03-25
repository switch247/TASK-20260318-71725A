# Security and Compliance Controls

## Implemented Controls

- JWT access and refresh token strategy with server-side refresh revocation.
- Password complexity validation and login lockout controls.
- Sensitive field encryption helper service for contact and identity fields.
- Role and organization-scoped authorization checks for protected APIs.
- Attachment upload controls:
  - Local MIME whitelist
  - Maximum file size (`<= 20MB`)
  - SHA-256 fingerprint deduplication
  - Organization ownership checks on reads
- Immutable audit records with chained hashes (`previous_hash` and `current_hash`).

## HTTPS Requirement

Deployment must terminate TLS at reverse proxy/load balancer and forward trusted headers.
Application enforces HTTPS for API routes and rejects non-HTTPS transport context.

## Logging Rules

- No secrets or plaintext sensitive values in logs.
- Log authentication, data changes, export tasks, and approval decisions.
- Include request correlation metadata where available.
