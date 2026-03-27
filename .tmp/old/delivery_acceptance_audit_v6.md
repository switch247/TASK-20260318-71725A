# Delivery Acceptance / Project Architecture Audit Report

Project: `pure_backend`  
Audit date: 2026-03-26  
Scope: static code + local test execution (no Docker per instruction)

## Environment Limits
- Docker-based startup in README was **not executed** because the audit rule says: "Do not start Docker or related commands." 
- Therefore, runtime verification is split into:
  - **Confirmed**: Python/pytest execution and endpoint-level behavior in test harness.
  - **Unconfirmed**: Full Docker startup parity with README and PostgreSQL runtime behavior in this environment.

## Severity Summary
- **Blocker**
  - README-documented test command is non-functional in this environment (`run_tests.sh` as bash script on PowerShell), while direct `pytest` run also reports a failing test.
- **High**
  - Core security policy gap: account lockout status not enforced at login when `locked_until` has elapsed (status can remain `LOCKED` but login succeeds).
  - Core security policy gap: no API-level check to reject disabled users (`UserStatus.DISABLED`) in auth path.
  - Test suite has one failing test (`test_real_auth_flow`), weakening delivery confidence.
- **Medium**
  - RBAC permission matrix conflicts with stated business model (e.g., reviewer cannot upload attachments despite process requiring material upload in approval flow).
  - "Offline single environment" prompt asks PostgreSQL consistency, but tests/default dev flow largely rely on SQLite path; PostgreSQL behaviors remain only partially proven.
- **Low**
  - Documentation path mismatch in README (`./docs/api.md` etc. while docs are under repo-root `/docs`).

---

## 1. Hard Thresholds

### 1.1 Can the delivered product run and be verified?

#### 1.1.a Clear startup/execution instructions provided
- **Conclusion**: Pass
- **Reason**: README provides startup commands, service endpoints, and quality-gate instructions.
- **Evidence**:
  - `pure_backend/README.md:34-71`
  - `pure_backend/README.md:102-126`
- **Reproduction**:
  1. `cd pure_backend`
  2. `cp .env.example .env`
  3. `docker compose up --build` (not executed due audit constraint)

#### 1.1.b Can start/run without modifying core code
- **Conclusion**: Partial
- **Reason**: Python test run executes without code changes, but documented one-command gate `./run_tests.sh` is bash-targeted and produced no meaningful output on this PowerShell context; direct pytest shows a failing test.
- **Evidence**:
  - `pure_backend/run_tests.sh:1-54`
  - failing test output: `tests/API_tests/test_real_auth_flow.py:19`
- **Reproduction**:
  1. `cd pure_backend`
  2. `./run_tests.sh`
  3. `python -m pytest -q`

#### 1.1.c Actual run results match instructions
- **Conclusion**: Partial
- **Reason**: README says run quality gates via `./run_tests.sh`; in this environment it is not reliable, and direct `pytest` reports failure.
- **Evidence**:
  - `pure_backend/README.md:102-107`
  - `pure_backend/run_tests.sh:1-54`
  - failing test: `pure_backend/tests/API_tests/test_real_auth_flow.py:8-20`
- **Reproduction**:
  1. `cd pure_backend`
  2. `python -m pytest -q`

### 1.2 Prompt-theme deviation check

#### 1.2.a Centered around prompt business goals
- **Conclusion**: Pass
- **Reason**: Project implements identity/org/RBAC/process/analytics/export/governance/security modules explicitly aligned to prompt.
- **Evidence**:
  - Router composition: `pure_backend/src/api/v1/router.py:14-22`
  - Domain docs: `docs/design.md:15-24`
- **Reproduction**:
  1. Inspect `src/api/v1/endpoints/*`
  2. Inspect `src/models/*` and `src/services/*`

#### 1.2.b Strong relation to prompt theme
- **Conclusion**: Pass
- **Reason**: Feature sets map directly (workflow, metrics, data governance, audit, encryption, lockout, attachment checks).
- **Evidence**:
  - Workflow SLA/idempotency: `pure_backend/src/services/process_service.py:81-105,178-220`
  - Data governance checks: `pure_backend/src/services/governance_service.py:320-340`
  - Security controls: `pure_backend/src/services/security_service.py:50-68,121-147`
- **Reproduction**:
  1. Review above files/lines.

#### 1.2.c Core problem replaced/weakened/ignored
- **Conclusion**: Partial
- **Reason**: Mostly implemented, but some semantics are weakened (see Sections 4/5 findings: user status enforcement and RBAC-policy mismatch).
- **Evidence**:
  - Missing disabled-status check in login path: `pure_backend/src/services/auth_service.py:91-103`
  - Role matrix grants for attachment create/read flow: `pure_backend/src/services/seed_service.py:16-25`
- **Reproduction**:
  1. Inspect auth and permission seed code.

---

## 2. Delivery Completeness

### 2.1 Coverage of core requirements

#### 2.1.a Identity: register/login/logout/password recovery, username unique, password policy
- **Conclusion**: Pass
- **Reason**: Endpoints and policy exist; unique username DB constraint present.
- **Evidence**:
  - Auth endpoints: `pure_backend/src/api/v1/endpoints/auth.py:30-153`
  - Password policy: `pure_backend/src/core/security.py:3-7`
  - Username unique: `pure_backend/src/models/identity.py:24-27`
- **Reproduction**:
  1. Use `/api/v1/auth/register/login/logout/password/recovery/*`.

#### 2.1.b Organization create/join with org-level isolation
- **Conclusion**: Pass
- **Reason**: Org/membership models and dependency-based org-context enforcement are implemented.
- **Evidence**:
  - Org APIs: `pure_backend/src/api/v1/endpoints/organizations.py:15-44`
  - Membership enforcement: `pure_backend/src/api/v1/dependencies.py:46-56`
  - Membership model: `pure_backend/src/models/identity.py:44-71`
- **Reproduction**:
  1. Create org via `/organizations`
  2. Access org-scoped endpoint with/without `X-Organization-Id`.

#### 2.1.c Four-role RBAC with resource/action semantics
- **Conclusion**: Partial
- **Reason**: RBAC framework exists, but role grants do not fully align with process material upload/access expectations.
- **Evidence**:
  - Permission checks: `pure_backend/src/api/v1/dependencies.py:72-82`
  - Seed role permissions: `pure_backend/src/services/seed_service.py:6-31`
  - Attachment routes gated by process permissions: `pure_backend/src/api/v1/endpoints/security.py:17,41`
- **Reproduction**:
  1. Compare role grants in `seed_service.py` to attachment endpoint permission guards.

#### 2.1.d Operations analysis KPI dashboard and advanced search
- **Conclusion**: Pass
- **Reason**: Dashboard supports metric queries/pagination; advanced search covers appointments/patients/doctors/expenses.
- **Evidence**:
  - Dashboard API/service: `pure_backend/src/api/v1/endpoints/analytics.py:20-29`, `pure_backend/src/services/analytics_service.py:25-53`
  - Advanced search: `pure_backend/src/api/v1/endpoints/medical_ops.py:13-20`, `pure_backend/src/repositories/medical_ops_repository.py:12-96`
- **Reproduction**:
  1. POST `/analytics/dashboard`
  2. POST `/operations/search`.

#### 2.1.e Export whitelist + desensitization + traceable task records
- **Conclusion**: Pass
- **Reason**: Whitelist/policy JSON stored and applied; export task records and trace code persisted.
- **Evidence**:
  - Export task fields: `pure_backend/src/models/operations.py:48-78`
  - Apply whitelist/masking: `pure_backend/src/services/analytics_service.py:152-166,191-196`
  - Trace/event records: `pure_backend/src/services/analytics_service.py:98-123,219-230`
- **Reproduction**:
  1. POST `/analytics/exports`
  2. POST `/analytics/exports/{task_id}/execute`.

#### 2.1.f Process workflows: two types, branching, parallel/joint, SLA/reminders, full audit chain
- **Conclusion**: Pass
- **Reason**: Workflow type enum supports both types; conditional nodes, parallel/joint flags, SLA due date/reminders, and audit trail are implemented.
- **Evidence**:
  - Workflow types: `pure_backend/src/models/enums.py:23-26`
  - Branch/parallel/joint evaluation: `pure_backend/src/services/process_engine.py:60-115`
  - SLA/reminder: `pure_backend/src/services/process_service.py:104,178-220`
  - Audit trail: `pure_backend/src/models/process.py:86-99`
- **Reproduction**:
  1. Create definition with conditional/parallel/joint nodes.
  2. Submit instance and dispatch reminders.

#### 2.1.g Persistence and constraints (SQLAlchemy+PostgreSQL intent, unique indexes, idempotency, status enums, time indexes)
- **Conclusion**: Partial
- **Reason**: Models enforce many constraints/indexes; PostgreSQL target is configured, but runtime proof here is SQLite-heavy and Docker not executed.
- **Evidence**:
  - DB URL default PostgreSQL: `pure_backend/src/core/config.py:15-18`
  - Unique constraints: `pure_backend/src/models/identity.py:15,24`; `pure_backend/src/models/process.py:28-32`
  - 24h duplicate business-number handling: `pure_backend/src/repositories/process_repository.py:36-50`
- **Reproduction**:
  1. Inspect model constraints.
  2. Submit same business number within 24h.

#### 2.1.h Data governance: coding/data quality, error writeback, snapshots/version/rollback/lineage, daily backup, 30-day archive, retries<=3
- **Conclusion**: Pass
- **Reason**: Quality checks and error writeback implemented; snapshot/rollback/lineage and job scheduling with max 3 retries are present.
- **Evidence**:
  - Quality checks + detail error writeback: `pure_backend/src/services/governance_service.py:54-68,320-340`
  - Snapshot lineage fields: `pure_backend/src/models/governance.py:52-63`
  - Retry cap: `pure_backend/src/models/governance.py:76-77`
  - Backup/archive jobs: `pure_backend/src/services/governance_service.py:154-318`
- **Reproduction**:
  1. POST `/governance/imports`, `/governance/snapshots`, `/governance/jobs/bootstrap`, `/governance/jobs/execute`.

#### 2.1.i Security/compliance: encryption, response desensitization, HTTPS-only, immutable logs, lockout, upload validation, fingerprint dedup, ownership checks
- **Conclusion**: Partial
- **Reason**: Most controls are implemented, but account status check gaps reduce completeness (see High issues).
- **Evidence**:
  - Encryption helpers: `pure_backend/src/services/crypto_service.py:70-84`
  - Masking: `pure_backend/src/services/masking_service.py:4-27`
  - HTTPS middleware: `pure_backend/src/core/https.py:24-40`
  - Immutable logs: `pure_backend/src/models/security.py:57-69`, `pure_backend/src/services/operation_logger.py:63-89`
  - Lockout constants: `pure_backend/src/core/constants.py:5-7`
  - Upload validation/dedup: `pure_backend/src/services/security_service.py:50-75`
  - Ownership checks: `pure_backend/src/services/security_service.py:131-139`
- **Reproduction**:
  1. Exercise auth failures and login attempts.
  2. Upload files with boundary sizes and wrong business context.

### 2.2 0->1 delivery form

#### 2.2.a Not just snippets/local functions
- **Conclusion**: Pass
- **Reason**: Complete backend project structure with API/services/repos/models/tests/docs.
- **Evidence**:
  - Tree root and module layout from `pure_backend/src/*`, `pure_backend/tests/*`, `docs/*`
- **Reproduction**:
  1. Inspect file tree.

#### 2.2.b Mock/hardcoding replacing real logic without explanation
- **Conclusion**: Partial
- **Reason**: Some operational jobs are dry-run style summaries rather than real archival movement; acceptable for scope if documented, but production risk exists.
- **Evidence**:
  - Archive mode marks `"dry_run_summary"`: `pure_backend/src/services/governance_service.py:285`
- **Reproduction**:
  1. Execute governance jobs and inspect snapshot payload.

#### 2.2.c Complete project structure and docs
- **Conclusion**: Pass
- **Reason**: README + docs + Dockerfile + compose + tests provided.
- **Evidence**:
  - `pure_backend/README.md`
  - `pure_backend/Dockerfile`, `pure_backend/docker-compose.yml:1-28`
  - `docs/*.md`
- **Reproduction**:
  1. Inspect these files.

---

## 3. Engineering & Architecture Quality

### 3.1 Structure and module division

#### 3.1.a Clarity and responsibility separation
- **Conclusion**: Pass
- **Reason**: API/service/repository/model layering is clean and consistent.
- **Evidence**:
  - `docs/architecture.md:5-9`
  - `pure_backend/src/api`, `services`, `repositories`, `models`
- **Reproduction**:
  1. Trace one feature (e.g., process submit) across endpoint/service/repo.

#### 3.1.b Redundant/unnecessary files
- **Conclusion**: Partial
- **Reason**: Large checked-in artifacts (`__pycache__`, `.coverage`, `test.db`, mypy cache) exist and reduce repo cleanliness.
- **Evidence**:
  - e.g., `pure_backend/.coverage`, `pure_backend/test.db`, `pure_backend/src/**/__pycache__/*`
- **Reproduction**:
  1. `Get-ChildItem -Recurse -File` and inspect artifacts.

#### 3.1.c Excessive single-file stacking
- **Conclusion**: Pass
- **Reason**: Core logic is spread across domain-specific services/repositories; no monolith file observed.
- **Evidence**:
  - `pure_backend/src/services/*.py`
- **Reproduction**:
  1. Inspect service files by domain.

### 3.2 Maintainability/scalability awareness

#### 3.2.a Coupling/chaos
- **Conclusion**: Pass
- **Reason**: Dependency injection, repositories, and schema boundaries present; coupling is moderate.
- **Evidence**:
  - `pure_backend/src/api/v1/dependencies.py:19-82`
  - `pure_backend/src/services/*`
- **Reproduction**:
  1. Evaluate endpoint-level dependencies and service entry points.

#### 3.2.b Room for extension vs hardcoding
- **Conclusion**: Partial
- **Reason**: Extensible structure exists, but a few behaviors are rigid/hardcoded (allowed MIME set, KPI mapping table, dry-run archive semantics).
- **Evidence**:
  - MIME allowlist hardcoded: `pure_backend/src/services/security_service.py:54-60`
  - KPI mapping hardcoded: `pure_backend/src/services/analytics_service.py:248-255`
- **Reproduction**:
  1. Review hardcoded lists/maps in service code.

---

## 4. Engineering Details & Professionalism

### 4.1 Error handling, logging, validation, API design

#### 4.1.a Error handling robustness
- **Conclusion**: Pass
- **Reason**: Centralized custom error envelope and global unhandled-exception handling implemented.
- **Evidence**:
  - Error model: `pure_backend/src/core/errors.py:6-35`
  - Handlers: `pure_backend/src/main.py:59-75`
- **Reproduction**:
  1. Trigger validation/notfound/forbidden errors.

#### 4.1.b Logging quality
- **Conclusion**: Pass
- **Reason**: Structured operation logging + immutable audit chain for mutations.
- **Evidence**:
  - Logger service: `pure_backend/src/services/operation_logger.py:19-90`
  - Operation log model: `pure_backend/src/models/security.py:35-55`
- **Reproduction**:
  1. Perform mutating API call and query operation logs.

#### 4.1.c Critical input/boundary validation
- **Conclusion**: Partial
- **Reason**: Strong validation across schemas/uploads, but security-critical status checks in auth are incomplete.
- **Evidence**:
  - Strong schema checks: `pure_backend/src/schemas/*.py`
  - Upload checks: `pure_backend/src/services/security_service.py:50-68`
  - Missing status check at login: `pure_backend/src/services/auth_service.py:91-103`
- **Reproduction**:
  1. Observe login path and user status handling.

### 4.2 Real service vs demo
- **Conclusion**: Partial
- **Reason**: Mostly product-like, but a few runtime behaviors are demo-like (governance dry-run archive summaries, local file export/attachment storage) and need ops hardening for production.
- **Evidence**:
  - Dry-run archive payload: `pure_backend/src/services/governance_service.py:285`
  - Local storage paths: `pure_backend/src/services/security_service.py:77-81`, `pure_backend/src/services/analytics_service.py:198-213`
- **Reproduction**:
  1. Execute exports and governance jobs.

---

## 5. Requirement Understanding & Adaptation

### 5.1 Business-goal and implicit-constraint fidelity

#### 5.1.a Core goals accurately achieved
- **Conclusion**: Partial
- **Reason**: Most goals are implemented end-to-end, but critical auth/status and role-policy fit gaps remain.
- **Evidence**:
  - Broad domain coverage: `src/api/v1/router.py:15-22`
  - Lockout/status logic gap: `src/services/auth_service.py:359-387` + missing status gate in login.
- **Reproduction**:
  1. Review role/lockout enforcement in auth service.

#### 5.1.b Requirement semantic misunderstandings
- **Conclusion**: Partial
- **Reason**: Reviewer/general-user capability boundaries around process attachments are semantically inconsistent with process material upload/access expectations.
- **Evidence**:
  - Security attachment endpoints require process create/review: `src/api/v1/endpoints/security.py:17,41`
  - Seed grants omit reviewer `process:create`: `src/services/seed_service.py:16-20`
- **Reproduction**:
  1. Compare role grants to attachment endpoint requirements.

#### 5.1.c Key constraints changed/ignored without explanation
- **Conclusion**: Partial
- **Reason**: PostgreSQL/transaction consistency intent exists but executable validation in this run is SQLite-first and Docker-unverified.
- **Evidence**:
  - Prompted DB target: config `src/core/config.py:15-18`
  - Tests force SQLite: `tests/API_tests/conftest.py:11,25`; `tests/unit_tests/conftest.py:11,14`
- **Reproduction**:
  1. Inspect conftest DB URL overrides.

---

## 6. Aesthetics (Full-stack / Front-end only)

### 6.1 Visual/interaction design
- **Conclusion**: N/A
- **Reason**: Delivery is backend API service; no custom frontend/UI implementation under audit scope.
- **Evidence**:
  - No frontend app structure present; endpoints only.
- **Reproduction**:
  1. Inspect repository contents.

---

## 7. Security & Logs (Focused Audit)

### 7.1 Authentication and route authorization
- **Conclusion**: Partial
- **Reason**: JWT + permission dependencies are implemented, but user-status enforcement is incomplete.
- **Evidence**:
  - Token decode + user lookup: `src/api/v1/dependencies.py:23-43`
  - Missing disabled-status rejection in login: `src/services/auth_service.py:91-103`
  - Lockout only checks `locked_until`: `src/services/auth_service.py:359-363`
- **Reproduction**:
  1. Set user status to disabled/locked-without-future-locktime and test login.

### 7.2 Object-level authorization (IDOR) and data isolation
- **Conclusion**: Pass
- **Reason**: Attachment read checks both org ownership and business-number ownership.
- **Evidence**:
  - `src/services/security_service.py:131-139`
  - process-business linkage: `src/repositories/security_repository.py:30-37`
- **Reproduction**:
  1. Read same attachment with wrong `business_number` -> 403.

### 7.3 Sensitive data exposure and desensitization
- **Conclusion**: Partial
- **Reason**: Masking exists for export preview and `/auth/me` for certain roles; but policy coverage is selective and may need centralized guarantee across all response paths.
- **Evidence**:
  - Masking service: `src/services/masking_service.py:4-27`
  - Me endpoint masking branch: `src/api/v1/endpoints/auth.py:170-173`
  - Export masking: `src/services/analytics_service.py:137-166`
- **Reproduction**:
  1. Query with reviewer role and inspect masked fields.

### 7.4 Immutable logging and traceability
- **Conclusion**: Pass
- **Reason**: Mutable operation logs + chained immutable logs are written on mutating paths.
- **Evidence**:
  - `src/services/operation_logger.py:40-89`
  - `src/models/security.py:57-69`
- **Reproduction**:
  1. Perform mutation and check increased immutable log count.

---

## 8. Testing Coverage Evaluation (Static Audit)

### 8.1 Overview
- **Framework/entry points**:
  - Pytest config: `pure_backend/pyproject.toml:21-25`
  - Unit tests: `pure_backend/tests/unit_tests/*`
  - API tests: `pure_backend/tests/API_tests/*`
- **README commands**:
  - `pure_backend/README.md:102-107`
- **Observed execution**:
  - `python -m pytest -q` => 1 failing test (`test_real_auth_flow`)

### 8.2 Coverage Mapping Table

| Requirement / Risk | Test Case(s) | Key Assertion | Coverage Status |
|---|---|---|---|
| Register/login/password policy | `tests/API_tests/test_auth_api.py:1-80` | 200/400/401 behavior | Full |
| Password recovery flow | `tests/API_tests/test_auth_api.py:83-126` | token flow + reset | Full |
| Org isolation membership deny | `tests/API_tests/test_rbac_matrix.py:57-70` | outsider gets 403 | Full |
| RBAC role matrix | `tests/API_tests/test_rbac_matrix.py:1-55` | admin/reviewer/general/auditor behavior | Basic |
| Process idempotency conflict (409) | `tests/API_tests/test_conflicts_and_pagination.py:9-31` | second request 409 | Full |
| 24h duplicate business-number idempotent behavior | `tests/API_tests/test_process_api.py:40-53` | same ID returned | Basic |
| Process branch/parallel/joint | `tests/API_tests/test_process_api.py:81-226` + `tests/unit_tests/test_process_refactor_units.py:18-31` | node/task semantics | Full |
| SLA reminder + no duplicate reminder | `tests/API_tests/test_process_api.py:228-266` | second dispatch count=0 | Full |
| Analytics KPI and search | `tests/API_tests/test_analytics_operations_api.py:4-47,132-145` | KPI types/search payload | Full |
| Export whitelist + desensitization | `tests/API_tests/test_analytics_operations_api.py:102-129` | masked + whitelist filtering | Full |
| Governance quality checks | `tests/API_tests/test_governance_api.py:1-19` | failed rows > 0 | Basic |
| Governance snapshots/rollback/jobs | `tests/API_tests/test_governance_api.py:21-48`; `test_governance_execution.py` | snapshot/job assertions | Full |
| HTTPS enforcement | `tests/API_tests/test_https_enforcement.py:10-55` | 400/200 by proto/proxy | Full |
| Attachment security (size/type/dedup/IDOR context) | `tests/API_tests/test_security_api.py:12-289` | boundary + context + masking | Full |
| Global error envelope | `tests/API_tests/test_error_handling.py:7-21` | 500 envelope shape | Full |
| Operation/immutable logging | `tests/API_tests/test_operation_logging.py:6-89` | log records appended | Full |
| Pagination boundaries | `tests/API_tests/test_conflicts_and_pagination.py:33-64` | page/limit and invalid limit | Basic |
| 404 coverage | `tests/API_tests/test_security_api.py:153-159` | attachment not found 404 | Basic |
| 401 coverage | `tests/API_tests/test_auth_api.py:74-80` | login invalid password | Basic |
| 403 coverage | `tests/API_tests/test_rbac_matrix.py:16-70`; `test_process_api.py:268-277` | forbidden scenarios | Full |
| 409 coverage | `tests/API_tests/test_conflicts_and_pagination.py:9-31` | conflict status | Full |
| Concurrency/transactions | `tests/API_tests/test_conflicts_and_pagination.py:66-104` | parallel submit outcomes | Basic |

### 8.3 Security Coverage Audit (Auth / IDOR / Data Isolation)
- **Auth**: good path coverage, but no direct test that disabled users are rejected.
  - Evidence: no dedicated disabled-status login test in `tests/API_tests/test_auth_api.py`.
- **IDOR**: strong attachment business-context checks tested.
  - Evidence: `tests/API_tests/test_security_api.py:176-214`.
- **Data Isolation**: outsider org denial covered.
  - Evidence: `tests/API_tests/test_rbac_matrix.py:57-70`.

### 8.4 Overall test adequacy judgment
- **Conclusion**: Partial
- **Reason**: Breadth is strong, but one failing test and missing explicit coverage for disabled-user auth and some deep transaction edge-cases keep it below full acceptance.

---

## 9. Issue List with Grades

### [Blocker] B1 - Verification command mismatch / failing suite
- **Finding**: README quality-gate command is not reliable in this PowerShell run context; direct pytest run fails one test.
- **Evidence**:
  - `pure_backend/README.md:102-107`
  - `pure_backend/run_tests.sh:1-54`
  - `tests/API_tests/test_real_auth_flow.py:19`
- **Impact**: Delivery cannot be accepted as "fully verified" from instructions alone.
- **Suggestion**: Provide native PowerShell test script and ensure CI-local parity; fix failing test or underlying logic.

### [High] H1 - Disabled user status not enforced at login
- **Finding**: Login path validates lockout window and password but does not reject `UserStatus.DISABLED`.
- **Evidence**:
  - `pure_backend/src/services/auth_service.py:91-103`
- **Impact**: Disabled accounts may authenticate if password is valid.
- **Suggestion**: Explicitly reject non-active statuses before password verification.

### [High] H2 - Lockout semantics can be bypassed post-window without status reconciliation
- **Finding**: `_validate_lockout` only checks `locked_until > now`; if expired but status remains `LOCKED`, login can proceed.
- **Evidence**:
  - `pure_backend/src/services/auth_service.py:359-363`
  - status set on lockout: `pure_backend/src/services/auth_service.py:379-381`
- **Impact**: Status model and lockout policy can drift; inconsistent account state.
- **Suggestion**: normalize status when lock expires and enforce status check.

### [High] H3 - Test suite not fully green
- **Finding**: `test_real_auth_flow` fails (`register` returns 400).
- **Evidence**:
  - `pure_backend/tests/API_tests/test_real_auth_flow.py:8-20`
- **Impact**: Core acceptance confidence is reduced.
- **Suggestion**: isolate test data/state issue and enforce deterministic DB fixture isolation.

### [Medium] M1 - RBAC semantics around process material upload/access need alignment
- **Finding**: Reviewer role lacks `process:create` but attachment creation is guarded by `process:create`; this may conflict with real approval-material upload flow.
- **Evidence**:
  - Role grants: `pure_backend/src/services/seed_service.py:16-25`
  - Endpoint guard: `pure_backend/src/api/v1/endpoints/security.py:17`
- **Impact**: Business-role usability gap.
- **Suggestion**: align permission model to business semantics for who uploads/reads materials at each stage.

### [Medium] M2 - PostgreSQL consistency not fully runtime-proven in delivered verification path
- **Finding**: Target DB is PostgreSQL, but tests use SQLite, and Docker runtime was not executed in audit.
- **Evidence**:
  - Target DB config: `pure_backend/src/core/config.py:15-18`
  - Test DB override: `pure_backend/tests/API_tests/conftest.py:11,25`
- **Impact**: potential behavior gaps (indexes, transaction isolation, SQL dialect specifics).
- **Suggestion**: add PG-backed integration test profile (non-Docker allowed path if needed).

### [Low] L1 - README doc path references partially inconsistent
- **Finding**: README references `./docs/api.md` and `./docs/design.md` from `pure_backend/`, while primary docs are in repo-root `docs/`.
- **Evidence**:
  - `pure_backend/README.md:130-133`
  - existing docs under root: `docs/api-specs.md`, `docs/design.md`, etc.
- **Impact**: onboarding friction.
- **Suggestion**: normalize document paths in README.

---

## 10. Clause-by-Clause Acceptance Checklist

### 1. Hard Thresholds
- 1.1 Run/verify capability: **Partial**
- 1.2 Theme alignment: **Pass**

### 2. Delivery Completeness
- 2.1 Core requirements coverage: **Partial**
- 2.2 0->1 project form: **Pass**

### 3. Engineering & Architecture Quality
- 3.1 Structure/modularity: **Pass**
- 3.2 Maintainability/scalability: **Partial**

### 4. Engineering Details & Professionalism
- 4.1 Error/logging/validation/API detail: **Partial**
- 4.2 Product-grade maturity vs demo: **Partial**

### 5. Requirement Understanding & Adaptation
- 5.1 Requirement semantics/business fit: **Partial**

### 6. Aesthetics (frontend/full-stack)
- 6.1 Visual/interaction quality: **N/A**

---

## 11. Overall Judgment
- **Final Acceptance Verdict**: **Conditional Fail (Not yet acceptable as final delivery)**
- **Why**:
  1. One failing automated test in reported suite.
  2. High-severity auth-status enforcement gaps.
  3. Verification-command/runtime parity issues in current delivery instructions.

Once Blocker + High issues are resolved and suite is green under documented commands, this project is close to acceptance-level quality.
