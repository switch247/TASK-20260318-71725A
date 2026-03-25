# Patch Notes: Audit Fixes and Contract Clarifications

## Critical Changes

- Added uniform operation logging helper with append-only semantics.
- Added workflow conflict behavior (`409`) for idempotency collisions.
- Added snapshot rollback materialization by creating lineage-based restoration snapshot.
- Added maintenance job execution endpoint with retry-aware state transitions.
- Refactored process internals into parser/engine/handler modules.

## Pagination Conventions

- List endpoints use `page` and `limit` (1-based page).
- Response includes `count`, `total_count`, `page`, and `limit`.

## Compatibility Notes

- New `409` may be returned for conflicting idempotency submissions.
- Some list/search endpoints now include pagination fields in response.
