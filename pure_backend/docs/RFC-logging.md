# RFC: Operation Logging Schema and Retention

## Purpose

Define a uniform append-only operation logging model for mutating domain actions across services.

## Schema

Primary fields in `operation_logs`:

- `actor_user_id`
- `organization_id`
- `resource_type`
- `resource_id`
- `operation`
- `trace_id`
- `event_timestamp`
- `before_json` (optional)
- `after_json` (optional)

Legacy-compatible fields retained:

- `action`
- `resource`
- `request_id`
- `metadata_json`

## Write Semantics

- Logging is append-only.
- Logging is non-blocking for business transactions.
- Failures in logging path are swallowed and should be surfaced through monitoring.

## Retention Policy (baseline)

- Operational retention target: 90 days hot storage.
- Archive target: move to cold storage after 90 days.
- Compliance-sensitive domains may require longer retention by policy.

## Indexing Notes

- `organization_id + created_at` for tenant timeline queries.
- `trace_id` for request traceability.
- `resource_type`, `operation` for audit drill-down.
