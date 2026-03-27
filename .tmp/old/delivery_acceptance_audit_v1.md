# Delivery Acceptance / Project Architecture Audit (pure_backend)

Audit date: 2026-03-25

Scope: `pure_backend`

Method: static code/document review + non-Docker runtime verification (`pytest`, `ruff`, `mypy`, in-process health check, local `uvicorn` startup attempt)

---

## 1. Hard Thresholds

### 1.1 Can the delivered product run and be verified?

#### 1.1.a Clear startup/execution instructions provided?
- Conclusion: **Pass**
- Reason: README includes Docker and local startup commands, service URLs, health-check command, and quality-gate command.
- Evidence: `pure_backend/README.md:34`, `pure_backend/README.md:52`, `pure_backend/README.md:74`, `pure_backend/README.md:82`, `pure_backend/README.md:96`
- Reproduction steps:
  1. `cd pure_backend`
  2. `cp .env.example .env`
  3. Follow either Docker path (`docker compose up --build`) or local path (`pip install -r requirements.txt && uvicorn src.main:app --reload --host 0.0.0.0 --port 8000`).

#### 1.1.b Can it start/run without modifying core code?
- Conclusion: **Partial**
- Reason: Test and in-process API verification run successfully without code changes. Full local `uvicorn` startup fails in this environment because `.env` uses Docker hostname `db` for PostgreSQL, unavailable outside Docker.
- Evidence: `pure_backend/.env:13`, `pure_backend/README.md:61`, `pure_backend/src/main.py:24`, `pure_backend/src/main.py:26`; runtime result: `psycopg.OperationalError [Errno 11001] getaddrinfo failed`.
- Reproduction steps:
  1. `cd pure_backend`
  2. `python -m uvicorn src.main:app --host 127.0.0.1 --port 8011`
  3. Observe startup failure if DB host `db` is unreachable.

#### 1.1.c Do running results match delivery instructions?
- Conclusion: **Partial**
- Reason: Quality gates and tests pass as documented; health endpoint returns expected payload in TestClient verification. But README local-start path presumes DB availability; with provided `.env`, local non-Docker startup does not match out-of-the-box expectations.
- Evidence: `pure_backend/run_tests.sh:42`, `pure_backend/tests/integration/test_health.py:9`, `pure_backend/src/api/v1/endpoints/health.py:6`, `pure_backend/.env:13`
- Reproduction steps:
  1. `python -m pytest -q` (expected pass)
  2. `python -m ruff check . && python -m ruff format --check . && python -m mypy src` (expected pass)
  3. `python -c "from fastapi.testclient import TestClient; from src.main import app; r=TestClient(app).get('/api/v1/health'); print(r.status_code, r.json())"` (expected `200 {'status':'ok'}`)
  4. `python -m uvicorn src.main:app --host 127.0.0.1 --port 8011` (fails unless DB reachable).

### 1.2 Prompt theme deviation check

#### 1.2.a Is content centered on prompt business goals/scenarios?
- Conclusion: **Pass**
- Reason: Modules map directly to identity/org, RBAC, process approvals, analytics/export, governance, security/audit.
- Evidence: `pure_backend/src/api/v1/router.py:15`, `pure_backend/docs/design.md:15`, `pure_backend/docs/api.md:9`
- Reproduction steps:
  1. Review routers and docs.
  2. Confirm each prompt domain has endpoint group and model/service/repository coverage.

#### 1.2.b Strongly related implementation vs unrelated?
- Conclusion: **Pass**
- Reason: Domain model and API surface are purpose-built for hospital operation/process governance (appointments/patients/doctors/expenses + workflow + compliance).
- Evidence: `pure_backend/src/models/medical_ops.py:10`, `pure_backend/src/models/process.py:11`, `pure_backend/src/models/security.py:49`
- Reproduction steps:
  1. Inspect domain models.
  2. Cross-check with prompt's domain list.

#### 1.2.c Core problem substituted/weakened/ignored?
- Conclusion: **Partial**
- Reason: Core problem is mostly addressed, but several key constraints are weakened (workflow branching/parallelism not truly executed; HTTPS enforcement not implemented; object-level attachment ownership partly missing; desensitization not wired into API responses).
- Evidence: `pure_backend/src/services/process_service.py:173`, `pure_backend/src/services/security_service.py:86`, `pure_backend/src/main.py:18`, `pure_backend/src/services/analytics_service.py:100`
- Reproduction steps:
  1. Submit process definitions containing complex branches and observe no engine behavior beyond single fallback task.
  2. Call attachment read with same-org reviewer and unrelated business context (no process ownership validation).
  3. Check app middleware/config for HTTPS-only enforcement.

---

## 2. Delivery Completeness

### 2.1 Coverage of explicit core requirements

#### Identity, registration/login/logout/password recovery
- Conclusion: **Pass**
- Reason: Endpoints and service logic implemented; password reset included.
- Evidence: `pure_backend/src/api/v1/endpoints/auth.py:20`, `pure_backend/src/api/v1/endpoints/auth.py:34`, `pure_backend/src/api/v1/endpoints/auth.py:56`, `pure_backend/src/api/v1/endpoints/auth.py:63`
- Reproduction steps:
  1. `POST /api/v1/auth/register`
  2. `POST /api/v1/auth/login`
  3. `POST /api/v1/auth/logout`
  4. `POST /api/v1/auth/password/reset`

#### Username uniqueness + password policy (>=8, letters+numbers)
- Conclusion: **Pass**
- Reason: username unique constraint + validation on register/reset.
- Evidence: `pure_backend/src/models/identity.py:22`, `pure_backend/src/core/security.py:3`, `pure_backend/src/services/auth_service.py:35`, `pure_backend/src/services/auth_service.py:138`
- Reproduction steps:
  1. Register duplicate username; expect 400.
  2. Register weak password; expect 400.

#### User create/join organizations + org-level data isolation
- Conclusion: **Pass**
- Reason: create/join endpoints + membership enforcement through org header and permission dependency.
- Evidence: `pure_backend/src/api/v1/endpoints/organizations.py:15`, `pure_backend/src/api/v1/dependencies.py:47`, `pure_backend/src/services/authorization_service.py:11`
- Reproduction steps:
  1. Create org via `/organizations`.
  2. Join org via `/organizations/join`.
  3. Access org-scoped endpoint with non-member; expect 403.

#### Four-tier roles + resource/action permissions
- Conclusion: **Pass**
- Reason: role enum and permission seed matrix enforce resource-action checks.
- Evidence: `pure_backend/src/models/enums.py:4`, `pure_backend/src/services/seed_service.py:6`, `pure_backend/src/services/authorization_service.py:17`
- Reproduction steps:
  1. Seed roles.
  2. Attempt restricted action as lower privilege role; expect 403.

#### Operations dashboards + custom reports + key metrics scope
- Conclusion: **Partial**
- Reason: dashboard/report APIs and metric snapshots exist; however explicit KPI semantics (message reach, attendance anomaly, work-order SLA) are generic `metric_code` and not domain-enforced.
- Evidence: `pure_backend/src/api/v1/endpoints/analytics.py:11`, `pure_backend/src/models/operations.py:25`, `pure_backend/src/services/analytics_service.py:19`
- Reproduction steps:
  1. Create metric rows with `metric_code`.
  2. Query `/analytics/dashboard` with code list.
  3. Observe no dedicated KPI constraints.

#### Multi-criteria advanced search (appointments/patients/doctors/expenses)
- Conclusion: **Pass**
- Reason: resource-based search with filters for status/time/keyword/department/amount.
- Evidence: `pure_backend/src/schemas/medical_ops.py:7`, `pure_backend/src/repositories/medical_ops_repository.py:12`
- Reproduction steps:
  1. `POST /api/v1/operations/search` for each resource.
  2. Verify filtered results and org scoping.

#### Export with field whitelist + desensitization policy + traceability
- Conclusion: **Partial**
- Reason: whitelist/policy stored and trace records created; actual export execution and response desensitization path not integrated into endpoint responses.
- Evidence: `pure_backend/src/models/operations.py:58`, `pure_backend/src/models/operations.py:72`, `pure_backend/src/services/analytics_service.py:83`, `pure_backend/src/services/analytics_service.py:100`
- Reproduction steps:
  1. Create export task.
  2. Verify `trace_code` and task record persisted.
  3. Check no completed-file generation API in current delivery.

#### Process domain: two workflow types
- Conclusion: **Pass**
- Reason: enum supports resource application and credit change; definitions accept both.
- Evidence: `pure_backend/src/models/enums.py:23`, `pure_backend/src/services/process_service.py:36`
- Reproduction steps:
  1. Create definitions with `resource_application` and `credit_change`.

#### Conditional branching + joint/parallel signing
- Conclusion: **Fail**
- Reason: system stores definition JSON but execution always creates one fixed task (`review-node-1`) with `is_joint_sign=False`, `is_parallel=False`; no branch parser/executor.
- Evidence: `pure_backend/src/services/process_service.py:166`, `pure_backend/src/services/process_service.py:177`, `pure_backend/src/services/process_service.py:179`
- Reproduction steps:
  1. Submit definition JSON with branches/parallel nodes.
  2. Submit instance and inspect pending tasks; only one static task is generated.

#### SLA default 48h + reminders
- Conclusion: **Partial**
- Reason: default SLA due time implemented; reminder scheduling not implemented.
- Evidence: `pure_backend/src/core/config.py:28`, `pure_backend/src/services/process_service.py:77`
- Reproduction steps:
  1. Submit process instance; verify due_at ~48h default.
  2. Search code for reminder dispatch endpoints/jobs; none found.

#### Attachments + approval comments + full-chain audit trail + writeback result
- Conclusion: **Partial**
- Reason: attachment upload/read exists, task comments recorded, process audit trail appended, final result written on completion; but attachment-business ownership check is incomplete and immutable linkage is only in security audit log, not process trail.
- Evidence: `pure_backend/src/services/security_service.py:21`, `pure_backend/src/services/process_service.py:133`, `pure_backend/src/services/process_service.py:154`, `pure_backend/src/repositories/process_repository.py:98`
- Reproduction steps:
  1. Upload attachment and decide task with comment.
  2. Verify instance final_result_json on completion.
  3. Attempt cross-business read within same org (see security section).

#### Backend stack: FastAPI + SQLAlchemy + PostgreSQL
- Conclusion: **Pass**
- Reason: Framework/libs/config clearly match stack.
- Evidence: `pure_backend/requirements.txt:1`, `pure_backend/requirements.txt:3`, `pure_backend/requirements.txt:5`, `pure_backend/src/db/session.py:10`
- Reproduction steps:
  1. Install requirements.
  2. Start with configured PostgreSQL.

#### Core data models present
- Conclusion: **Pass**
- Reason: required entities exist (users, orgs, role auth, process definitions/instances/tasks, attachments, metric snapshots, dictionaries).
- Evidence: `pure_backend/src/models/identity.py:20`, `pure_backend/src/models/process.py:11`, `pure_backend/src/models/security.py:8`, `pure_backend/src/models/operations.py:11`, `pure_backend/src/models/governance.py:11`
- Reproduction steps:
  1. Inspect model declarations and tables.

#### Unique indexes + idempotency + status enums + time indexing
- Conclusion: **Pass**
- Reason: unique constraints/indexes and enums implemented; idempotency by key and 24h business-number window implemented.
- Evidence: `pure_backend/src/models/identity.py:13`, `pure_backend/src/models/process.py:29`, `pure_backend/src/repositories/process_repository.py:35`, `pure_backend/src/models/enums.py:28`
- Reproduction steps:
  1. Submit duplicate idempotency key; same instance returned.
  2. Submit same business number within 24h; prior instance returned.

#### Governance: coding rules + quality validation + writeback errors
- Conclusion: **Pass**
- Reason: missing/duplicate/out-of-bounds checks return row-level error message in batch details.
- Evidence: `pure_backend/src/services/governance_service.py:46`, `pure_backend/src/services/governance_service.py:130`, `pure_backend/src/models/governance.py:49`
- Reproduction steps:
  1. Call `/governance/imports` with empty/duplicate/out-of-bounds rows.
  2. Verify failed rows count and persisted details.

#### Version/snapshot/rollback/lineage
- Conclusion: **Partial**
- Reason: snapshot creation stores lineage reference; rollback endpoint returns success but does not restore payload to target domain state.
- Evidence: `pure_backend/src/models/governance.py:61`, `pure_backend/src/services/governance_service.py:92`, `pure_backend/src/services/governance_service.py:97`
- Reproduction steps:
  1. Create snapshot.
  2. Call rollback and observe status response only (no domain mutation logic).

#### Daily full backup + 30-day archive + retries<=3
- Conclusion: **Partial**
- Reason: bootstrap creates job records with max_retries=3 and expected job types; no actual scheduler/executor/failure compensation loop implemented.
- Evidence: `pure_backend/src/services/governance_service.py:103`, `pure_backend/src/services/governance_service.py:114`, `pure_backend/src/models/governance.py:77`
- Reproduction steps:
  1. Call `/governance/jobs/bootstrap`.
  2. Verify job records created.
  3. Confirm no runtime worker for execution/retry handling.

#### Sensitive field encrypted storage + role-based response desensitization
- Conclusion: **Partial**
- Reason: encryption utility and encrypted fields exist; API responses do not consistently apply role-based masking (masking helper not wired to endpoint returns).
- Evidence: `pure_backend/src/models/identity.py:28`, `pure_backend/src/services/crypto_service.py:79`, `pure_backend/src/services/masking_service.py:1`, `pure_backend/src/services/analytics_service.py:100`
- Reproduction steps:
  1. Inspect persisted encrypted columns.
  2. Review API serializers; observe no systematic role-conditioned masking pipeline.

#### HTTPS-only transmission
- Conclusion: **Fail**
- Reason: policy is documented only; no app-level HTTPS enforcement middleware/redirect/strict header checks in code.
- Evidence: `pure_backend/docs/security.md:18`, `pure_backend/src/main.py:18`
- Reproduction steps:
  1. Inspect app startup/middleware stack.
  2. Confirm no HTTPSRedirectMiddleware or equivalent enforcement.

#### Immutable operation logs + audit trails
- Conclusion: **Pass**
- Reason: operation logs plus hash-linked immutable audit log implemented.
- Evidence: `pure_backend/src/models/security.py:33`, `pure_backend/src/models/security.py:49`, `pure_backend/src/services/security_service.py:109`
- Reproduction steps:
  1. Append audit event.
  2. Validate `previous_hash`/`current_hash` chaining behavior.

#### Abnormal login risk control (5 failures/10min => 30min lock)
- Conclusion: **Pass**
- Reason: constants and lockout logic match threshold/window/duration.
- Evidence: `pure_backend/src/core/constants.py:5`, `pure_backend/src/core/constants.py:6`, `pure_backend/src/core/constants.py:7`, `pure_backend/src/services/auth_service.py:201`
- Reproduction steps:
  1. Repeatedly attempt wrong password 5 times.
  2. Observe lockout Unauthorized response and `locked_until` set.

#### Upload validation (format, <=20MB) + fingerprint dedup
- Conclusion: **Pass**
- Reason: MIME whitelist + max bytes + SHA-256 dedup path implemented.
- Evidence: `pure_backend/src/services/security_service.py:31`, `pure_backend/src/services/security_service.py:35`, `pure_backend/src/services/security_service.py:45`
- Reproduction steps:
  1. Upload 20MB file (accept).
  2. Upload 20MB+1 (reject 400).
  3. Re-upload same bytes under different name (deduplicated).

#### Attachment access validates org and business ownership; unauthorized reads denied
- Conclusion: **Partial**
- Reason: organization ownership enforced; business ownership (`process_instance_id` relationship/authorization) not verified on read.
- Evidence: `pure_backend/src/services/security_service.py:90`, `pure_backend/src/services/security_service.py:93`
- Reproduction steps:
  1. Read attachment from different org => 403.
  2. Same org but unrelated process context/read role can still read metadata (no business-level check).

### 2.2 0->1 deliverable form vs snippets/mocks

#### 2.2.a Complete project structure?
- Conclusion: **Pass**
- Reason: layered structure with docs, tests, configs, Docker, migrations.
- Evidence: `pure_backend/README.md:17`, `pure_backend/src/api/v1/router.py:14`, `pure_backend/tests/integration/test_health.py:1`
- Reproduction steps:
  1. List directories and inspect layer boundaries.

#### 2.2.b Basic documentation provided?
- Conclusion: **Pass**
- Reason: README + architecture/design/security/operations docs available.
- Evidence: `pure_backend/README.md:126`, `pure_backend/docs/design.md:1`, `pure_backend/docs/security.md:1`
- Reproduction steps:
  1. Review docs index in README.

#### 2.2.c Mock/hardcode replacement risk?
- Conclusion: **Partial**
- Reason: core logic is mostly real, but workflow execution and governance rollback/backup execution are simplified (logic stubs) without explicit limitations in API contracts.
- Evidence: `pure_backend/src/services/process_service.py:173`, `pure_backend/src/services/governance_service.py:92`, `pure_backend/src/services/governance_service.py:100`
- Reproduction steps:
  1. Exercise complex workflow and rollback/backup expectations.
  2. Observe simplified behavior.

Mock handling statement:
- No third-party payment integration appears in scope; thus no payment-mock defect applicable.

---

## 3. Engineering & Architecture Quality

### 3.1 Structure/module division reasonableness

#### 3.1.a Clear structure and separated responsibilities?
- Conclusion: **Pass**
- Reason: API->Service->Repository->Model split is clean and consistent.
- Evidence: `pure_backend/docs/architecture.md:5`, `pure_backend/src/api/v1/endpoints/process.py:16`, `pure_backend/src/services/process_service.py:24`, `pure_backend/src/repositories/process_repository.py:15`
- Reproduction steps:
  1. Follow one request path from endpoint to repository.

#### 3.1.b Redundant/unnecessary files?
- Conclusion: **Partial**
- Reason: some modules are unused/underused in runtime paths (e.g., `OrganizationRepository`, `ApiErrorResponse` schema, masking preview method not endpoint-bound).
- Evidence: `pure_backend/src/repositories/organization_repository.py:7`, `pure_backend/src/schemas/common.py:4`, `pure_backend/src/services/analytics_service.py:100`
- Reproduction steps:
  1. Compare coverage report for untouched modules.

#### 3.1.c Excessive single-file stacking?
- Conclusion: **Pass**
- Reason: no monolithic file; largest services are manageable.
- Evidence: `pure_backend/src/services/auth_service.py:29`, `pure_backend/src/services/process_service.py:24`
- Reproduction steps:
  1. Inspect file sizes and class boundaries.

### 3.2 Maintainability/scalability awareness

#### 3.2.a Coupling/chaos risk?
- Conclusion: **Pass**
- Reason: dependency injection + repository pattern keeps coupling moderate.
- Evidence: `pure_backend/src/api/v1/dependencies.py:59`, `pure_backend/src/services/authorization_service.py:8`
- Reproduction steps:
  1. Swap dependency overrides in tests; observe manageable isolation.

#### 3.2.b Expansion room vs hardcoding?
- Conclusion: **Partial**
- Reason: architecture supports growth, but critical engines (workflow branching/reminders, governance rollback executor) are currently hardcoded/minimal.
- Evidence: `pure_backend/src/services/process_service.py:173`, `pure_backend/src/services/governance_service.py:97`
- Reproduction steps:
  1. Attempt advanced process scenarios and inspect generated tasks/state changes.

---

## 4. Engineering Details & Professionalism

### 4.1 Error handling, logging, validation, API design

#### 4.1.a Error handling reliability and UX
- Conclusion: **Pass**
- Reason: custom domain exceptions normalized to envelope `{code,message,details}` and mapped status codes.
- Evidence: `pure_backend/src/core/errors.py:4`, `pure_backend/src/main.py:34`, `pure_backend/src/main.py:41`
- Reproduction steps:
  1. Trigger validation/unauthorized errors and inspect response JSON format.

#### 4.1.b Logging quality
- Conclusion: **Partial**
- Reason: central logging configured and unhandled exceptions logged; operation/audit logs exist, but request correlation IDs and structured security audit breadth are limited.
- Evidence: `pure_backend/src/core/logging.py:5`, `pure_backend/src/main.py:46`, `pure_backend/src/services/security_service.py:126`
- Reproduction steps:
  1. Trigger unhandled exception (or inspect handler).
  2. Create attachment and audit event; inspect persisted logs.

#### 4.1.c Critical validation and boundaries
- Conclusion: **Pass**
- Reason: strong request schema validation, password policy, upload checks, lockout checks, idempotency handling.
- Evidence: `pure_backend/src/schemas/auth.py:11`, `pure_backend/src/services/auth_service.py:35`, `pure_backend/src/services/security_service.py:31`, `pure_backend/src/repositories/process_repository.py:35`
- Reproduction steps:
  1. Send invalid payloads for auth/process/security endpoints.

### 4.2 Real product/service vs demo-level

#### 4.2.a Overall production-likeness
- Conclusion: **Partial**
- Reason: strong baseline (RBAC, audit hash chain, tests, typing/lint), but notable functional gaps in advanced workflow, HTTPS enforcement, and governance execution keep it short of full production completeness.
- Evidence: `pure_backend/run_tests.sh:42`, `pure_backend/src/services/process_service.py:166`, `pure_backend/src/main.py:18`, `pure_backend/src/services/governance_service.py:100`
- Reproduction steps:
  1. Verify quality gates pass.
  2. Exercise advanced requirements and observe missing parts.

---

## 5. Requirement Understanding & Adaptation

### 5.1 Business-goal and implicit-constraint response

#### 5.1.a Core business goals achieved?
- Conclusion: **Partial**
- Reason: major domains are implemented with executable APIs and persistence, but several compliance/process constraints are incomplete.
- Evidence: `pure_backend/src/api/v1/router.py:15`, `pure_backend/src/services/process_service.py:173`, `pure_backend/src/main.py:18`
- Reproduction steps:
  1. Validate end-to-end on covered domains.
  2. Check uncovered constraints in security/process governance.

#### 5.1.b Requirement semantic misunderstandings?
- Conclusion: **Partial**
- Reason: prompt expects object-level attachment ownership check and advanced workflow engine behavior; implementation currently simplifies both.
- Evidence: `pure_backend/src/services/security_service.py:90`, `pure_backend/src/services/process_service.py:179`
- Reproduction steps:
  1. Review attachment read authorization path.
  2. Review workflow task generation for complex definitions.

#### 5.1.c Key constraints changed/ignored without explanation?
- Conclusion: **Fail**
- Reason: HTTPS-only enforcement and reminder/parallel-branch execution are not implemented despite being key constraints; docs mention policy but runtime enforcement absent.
- Evidence: `pure_backend/docs/security.md:18`, `pure_backend/src/main.py:18`, `pure_backend/src/services/process_service.py:166`
- Reproduction steps:
  1. Search middleware/transport enforcement and workflow execution logic.

---

## 6. Aesthetics (Full-stack / Front-end)

### 6.1 Visual/interactions quality
- Conclusion: **N/A**
- Reason: This delivery is backend-only API service with no front-end assets.
- Evidence: `pure_backend/src/main.py:18`, `pure_backend/README.md:3`
- Reproduction steps:
  1. Inspect repository for UI/front-end modules (none).

---

## Security & Logs Focused Findings

### Authentication
- Conclusion: **Pass**
- Reason: JWT access/refresh with refresh revocation and lockout controls implemented.
- Evidence: `pure_backend/src/services/auth_service.py:72`, `pure_backend/src/services/auth_service.py:109`, `pure_backend/src/services/auth_service.py:196`
- Reproduction steps:
  1. Login, refresh, logout, reuse revoked refresh token.

### Route-level authorization (RBAC)
- Conclusion: **Pass**
- Reason: permission dependency + role-permission table + membership enforcement.
- Evidence: `pure_backend/src/api/v1/dependencies.py:59`, `pure_backend/src/services/authorization_service.py:17`, `pure_backend/src/services/seed_service.py:6`
- Reproduction steps:
  1. Attempt restricted endpoints with different roles.

### Object-level authorization (IDOR)
- Conclusion: **Partial** (**High risk**) 
- Reason: Attachment reads validate org only, not business ownership/process association or per-object grant.
- Evidence: `pure_backend/src/services/security_service.py:86`, `pure_backend/src/services/security_service.py:90`
- Reproduction steps:
  1. As same-org reviewer, request attachment ID not tied to your business context; currently no business ownership check.

### Data isolation
- Conclusion: **Pass**
- Reason: org header + membership check + org predicates in repositories.
- Evidence: `pure_backend/src/api/v1/dependencies.py:47`, `pure_backend/src/repositories/process_repository.py:24`, `pure_backend/src/repositories/medical_ops_repository.py:26`
- Reproduction steps:
  1. Use non-member token with target org header and verify 403.

### Sensitive data exposure/logging
- Conclusion: **Partial**
- Reason: encrypted storage utilities and columns exist, but no centralized response desensitization pipeline; logging policy mostly doc-level.
- Evidence: `pure_backend/src/models/identity.py:28`, `pure_backend/src/services/crypto_service.py:79`, `pure_backend/src/services/analytics_service.py:100`, `pure_backend/docs/security.md:23`
- Reproduction steps:
  1. Inspect sensitive fields at model/API layers.
  2. Verify role-based masking is not globally enforced in response path.

---

## Testing Coverage Evaluation (Static Audit)

### Overview (framework, entry points, README commands)
- Framework: `pytest` + FastAPI TestClient + coverage (`pyproject` addopts).
- Entry points: integration tests under `tests/integration`, unit tests under `tests/unit`.
- README command: `./run_tests.sh` runs `ruff`, `ruff format --check`, `mypy`, `pytest`.
- Evidence: `pure_backend/pyproject.toml:23`, `pure_backend/pyproject.toml:24`, `pure_backend/run_tests.sh:42`, `pure_backend/README.md:96`

### Coverage mapping table

| Requirement / Risk | Test case(s) | Assertion focus | Coverage status |
|---|---|---|---|
| Health startup path | `tests/integration/test_health.py:6` | 200 + `{"status":"ok"}` | Full |
| Registration happy path | `tests/integration/test_auth_api.py:1` | 200, user fields returned | Full |
| Password complexity | `tests/integration/test_auth_api.py:18` | weak pwd -> 400 | Full |
| Email validation boundary | `tests/integration/test_auth_api.py:33`, `tests/unit/test_auth_schema_validation.py:29` | empty valid, invalid rejected | Full |
| Login happy/error | `tests/integration/test_auth_api.py:61`, `tests/integration/test_auth_api.py:74` | success token, wrong pwd 401 | Basic |
| Login lockout risk-control | `tests/integration/test_security_api.py:107` | 5 fails -> locked_until set | Full |
| RBAC matrix | `tests/integration/test_rbac_matrix.py:1` | role allow/deny 200/403 | Full |
| Org isolation (membership) | `tests/integration/test_rbac_matrix.py:57` | outsider denied 403 | Full |
| Process submit/idempotency | `tests/integration/test_process_api.py:15`, `tests/integration/test_process_api.py:32` | same id for duplicate key | Full |
| Process decision flow | `tests/integration/test_process_api.py:47` | pending tasks + approve flow | Basic |
| Analytics dashboard/report/export | `tests/integration/test_analytics_operations_api.py:4`, `tests/integration/test_analytics_operations_api.py:19`, `tests/integration/test_analytics_operations_api.py:34` | success + expected fields | Basic |
| Advanced search | `tests/integration/test_analytics_operations_api.py:51` | doctors query success | Basic |
| Governance quality checks | `tests/integration/test_governance_api.py:1` | failed rows count | Basic |
| Snapshot + rollback API | `tests/integration/test_governance_api.py:21` | response status only | Insufficient |
| Job bootstrap retry cap | `tests/integration/test_governance_api.py:42` | max_retries==3 | Basic |
| Attachment size boundary | `tests/integration/test_security_api.py:12`, `tests/integration/test_security_api.py:34` | 20MB pass, >20MB fail | Full |
| Attachment dedup fingerprint | `tests/integration/test_security_api.py:54` | second upload deduplicated | Full |
| Attachment not found 404 | `tests/integration/test_security_api.py:86` | 404 path | Basic |
| Immutable audit append | `tests/integration/test_security_api.py:92` | hash length, audit id | Basic |
| 401/403/404/409 error-path baseline | Various; no explicit 409 assertions | 401/403/404 covered, 409 missing | Insufficient |
| Pagination boundaries | No tests found | N/A | Missing |
| Concurrency/transaction rollback | No stress/race tests | N/A | Missing |
| IDOR object ownership checks | No explicit tests for cross-object same-org access | N/A | Missing |

### Security coverage audit (Auth, IDOR, Data Isolation)
- Auth coverage: **Basic/Good** (register/login lockout tested).
- Data isolation coverage: **Good** (cross-org membership denied test exists).
- IDOR coverage: **Insufficient** (no test asserting business ownership beyond org boundary for attachments/process objects).
- Evidence: `pure_backend/tests/integration/test_auth_api.py:61`, `pure_backend/tests/integration/test_security_api.py:107`, `pure_backend/tests/integration/test_rbac_matrix.py:57`, `pure_backend/tests/integration/test_security_api.py:86`

### Overall testing sufficiency judgment
- Conclusion: **Partial**
- Reason: suite is substantial and passing (35 tests, ~87% line coverage), but misses critical risk classes (IDOR same-org object ownership, branch/parallel workflow semantics, reminder/HTTPS enforcement, concurrency/transaction conflict behavior, explicit 409 scenarios).
- Evidence: coverage output from `pytest -q`; `pure_backend/tests/integration/test_process_api.py:32`, `pure_backend/src/services/process_service.py:166`

---

## Issue List with Severity

### Blocker
1. **None confirmed** (environment-limited runtime issue is not counted as project defect per rule).

### High
1. **Missing business-level object authorization on attachment reads (IDOR risk)**
   - Evidence: `pure_backend/src/services/security_service.py:90`
2. **Conditional branching / joint / parallel workflow execution not implemented**
   - Evidence: `pure_backend/src/services/process_service.py:173`
3. **HTTPS-only not technically enforced in app runtime**
   - Evidence: `pure_backend/src/main.py:18`, `pure_backend/docs/security.md:18`

### Medium
1. **Data rollback endpoint does not perform true rollback semantics**
   - Evidence: `pure_backend/src/services/governance_service.py:92`
2. **Backup/archive/retry are only bootstrapped job records, not executed/compensated**
   - Evidence: `pure_backend/src/services/governance_service.py:100`
3. **Role-based response desensitization helper is not integrated across API responses**
   - Evidence: `pure_backend/src/services/analytics_service.py:100`

### Low
1. **Local non-Docker startup instructions are fragile with Docker-only DB hostname in `.env`**
   - Evidence: `pure_backend/.env:13`, `pure_backend/README.md:61`
2. **Deprecated FastAPI startup event style**
   - Evidence: `pure_backend/src/main.py:24`

---

## Environment Limits (Non-defect Boundaries)

- Docker was not started per instruction.
- Confirmed limitation: local startup failed because configured DB host `db` is unreachable outside Docker in current environment.
- This is documented as environment/runtime setup boundary, not core code defect.

Reproduce locally with Docker (user side):
1. `cd pure_backend`
2. `cp .env.example .env`
3. `docker compose up --build`
4. `curl http://localhost:8000/api/v1/health`

Reproduce locally without Docker (user side):
1. Ensure PostgreSQL is reachable and set `DATABASE_URL` to local host/service.
2. `pip install -r requirements.txt`
3. `uvicorn src.main:app --reload --host 0.0.0.0 --port 8000`

---

## Final Acceptance Judgment

- **Hard Threshold 1.1 (runnability): Partial**
- **Hard Threshold 1.2 (theme alignment): Pass (with notable gaps)**
- **Delivery completeness: Partial**
- **Engineering quality: Pass/Partial**
- **Professional details: Pass/Partial**
- **Requirement understanding/adaptation: Partial**
- **Testing sufficiency: Partial**

Overall decision: **Conditional Acceptance (not full pass)**

Rationale:
- The project is a real, runnable backend with substantial scope coverage and good engineering baseline.
- It does not fully satisfy several explicit prompt-critical constraints (advanced workflow semantics, strict HTTPS enforcement, and complete object-level authorization/business ownership checks), so full acceptance is not yet justified.
