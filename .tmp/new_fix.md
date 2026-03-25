Critical Issues and Required Changes

Goal
- Produce code changes, refactors, and tests to address the audit issues listed below. Make incremental, reviewable commits and include clear PR notes and tests. Do not modify existing top-level docs; create new files only when requested.

Priority order (critical -> medium -> low)
1. Uniform immutable operation logging across all mutating paths (HIGH)
2. Materialized rollback semantics and operational backup/archive execution pipeline (HIGH)
3. Split and refactor large service `process_service.py` into smaller modules with clear single responsibilities (HIGH)
4. Add tests for `409` conflict behavior, pagination boundaries, and concurrency/transaction race conditions (HIGH)
5. Expand desensitization/masking to all sensitive-response paths, not just export previews (MEDIUM)
6. Remove or mark underused/redundant modules (e.g., `organization_repository.py`) or document why they remain (MEDIUM)
7. Add DB indexes / query optimizations for hot paths and document them (MEDIUM)
8. Improve operational logging, metrics, and alerting (LOW)
9. Add missing pagination and API contract docs for endpoints that return lists (LOW)

For each item implement:
- A one-line summary comment at the top of each changed file explaining the change.
- Unit and API tests that cover the new behavior and the original expected behavior.
- Migrations when schema changes are required; keep them small and idempotent.
- If behavior changes could affect clients, add a short compatibility note in the PR description.

Detailed tasks & acceptance criteria

1) Uniform immutable operation logging (HIGH)
- Task: Add an `operation_log` table/model and a small `operation_logger` helper used by services/repositories when mutating domain entities (create/update/delete/restore/archive). Integrate into `auth_service`, `process_service`, `governance_service`, `security_service`, and attachment flows.
- Acceptance: Every mutating API call writes an operation log record with `actor_id`, `organization_id`, `resource_type`, `resource_id`, `operation`, `timestamp`, `before` (JSON, optional), `after` (JSON, optional), and `trace_id` headers when present. Tests must assert logs are written for a sample of endpoints.
- Notes: Operation logs should be append-only and not cause transaction rollbacks on failure (log failures should be retried/handled separately).

2) Materialized rollback & backup/archive pipeline (HIGH)
- Task: Implement rollback that actually restores data from snapshot/backup objects rather than just returning status. Add a background job runner or synchronous executor for small restores. Implement `backup_archive` job execution semantics with retry(3) and compensation.
- Acceptance: Create snapshot, mutate data, call rollback endpoint and assert DB state is restored to snapshot in tests. Implement basic job record state machine and unit tests for job retries and compensation path.

3) Refactor `process_service.py` (HIGH)
- Task: Break `process_service.py` into `process_parser.py`, `process_engine.py`, `process_handlers.py` or similar, isolating parsing, evaluation, and persistence. Keep public API of service stable where possible and add adapters for changed internal APIs.
- Acceptance: All existing tests pass; new unit tests cover parsing/evaluation in isolation. PR must include a short refactor plan and file map.

4) Tests for conflicts, pagination, concurrency (HIGH)
- Task: Add tests that explicitly cover `409` conflict cases (duplicate idempotency keys, unique constraints), pagination boundary behaviors (limit=0, limit=1, page beyond last), and concurrency tests (simulate two parallel submits that touch same resource). Use database fixtures and transaction isolation to reproduce race conditions.
- Acceptance: New tests fail on current code if issue present, then pass after fixes. Document test strategy in a short README entry.

5) Expand desensitization across responses (MEDIUM)
- Task: Implement a response-masking layer or serializer hooks that apply role-based masking consistently for user/attachment/operation data. Centralize masking logic in `masking_service` so all endpoints use it.
- Acceptance: Export preview tests remain passing; add tests for other endpoints verifying masked fields are not returned to unauthorized roles.

6) Underused modules: identify & act (MEDIUM)
- Task: Locate underused modules (example: `organization_repository.py`), either remove them if unused, add TODOs and documentation if kept for future use, or write simple integration tests if they should be used.
- Acceptance: No unreferenced files left without justification; PR includes rationale for removal or retention.

7) DB indexes & query optimization (MEDIUM)
- Task: Add suggested indexes for hot queries (process lookup by idempotency key, attachment fingerprint, operations by org+time) with migrations and explain cost/benefit.
- Acceptance: Migration + brief notes; ensure tests still pass.

8) Operational logging & metrics (LOW)
- Task: Add structured logs for major events with trace IDs; add basic counters (requests, failures, job runs) and a `/metrics` endpoint or export stub.
- Acceptance: Logs include trace IDs for sample endpoints; simple metrics endpoint returns JSON counters in tests.

9) Docs & API contracts (LOW)
- Task: Add short API contract notes (expected error codes including `409`), pagination conventions, and rollback semantics clarifications.
- Acceptance: New `docs/` markdown snippets added in the repo or a `docs/patches.md` file describing changes.

General instructions for the AI agent that implements fixes
- Work incrementally: implement one high-priority item at a time, run tests, open a PR for each logical change (or create a single branch with small commits if PRs are not available).
- Run `./run_tests.sh` and ensure linters/type checks/mypy/ruff pass before marking an item done.
- When adding new DB models or migrations, make them small and reversible; include migration names and descriptions.
- Write clear unit and API tests that reproduce the failure first, then implement the fix.
- Prefer minimal, low-risk changes that address root causes (e.g., add logging calls at service layer rather than scattering code across endpoints).
- Leave short TODO comments where further work is expected and add tests to cover the TODO surface where possible.

Extra improvements (not about running the code)
- Add missing pagination in list endpoints and standardize page/limit semantics.
- Add a small performance test for one hot query to justify index changes.
- Add a short checklist for acceptance criteria for governance features (snapshot/rollback/lineage).
- Add an RFC-style short file `RFC-logging.md` describing the operation log schema and retention policy.

Deliverables
- Branch or PR with incremental commits for each major change.
- Tests covering new behaviors and regression tests for existing features.
- Migration files for DB schema changes.
- Short PR description and acceptance checklist for reviewers.

Constraints & assumptions
- Do not start Docker containers or rely on live external services; tests and static analysis should be sufficient to verify changes.
- Keep backward compatibility where feasible; call out breaking changes explicitly.

If any item is blocked by missing information, comment in the PR describing the blocking assumption and list the minimal information needed.



