# System Design

## 1. Objectives

Build an enterprise-grade "Medical Operations and Process Governance Middle Platform API Service" with strict organization isolation, role-based controls, process traceability, data governance, and compliance-focused security.

## 2. Architecture Overview

- **API Layer**: FastAPI routers, request validation, response schema contracts.
- **Service Layer**: Domain business rules and transaction orchestration.
- **Repository Layer**: Data access and query abstraction.
- **Persistence Layer**: PostgreSQL + SQLAlchemy ORM + Alembic migrations.
- **Cross-Cutting**: RBAC authorization, JWT auth, audit logging, encryption, desensitization.

## 3. Domain Modules

- Identity and organization management
- Authorization and permissions
- Process/workflow engine
- Operations analytics and reporting
- Export management
- Data governance and lineage
- Security and compliance

## 4. Security Model

- JWT access/refresh strategy with refresh token revocation.
- Password policy and lockout controls.
- Field-level encryption for sensitive data.
- Role-based response desensitization.
- Immutable audit log for all critical operations.

## 5. Data Isolation Model

- All organization-scoped entities include `organization_id`.
- Access checks enforce org ownership in service and query layers.
- Attachment access validates org and business ownership.

## 6. Workflow Model

- Two workflow families: resource allocation and credit change approval.
- Supports conditional branches and parallel/joint approval tasks.
- Default SLA 48 hours, reminder scheduling, and overdue tracking.
- Idempotent submission key with 24-hour business number window.

## 7. Governance and Reliability

- Import-time data quality checks (missing, duplicate, out-of-bounds).
- Snapshot/version/rollback mechanisms and lineage traceability.
- Daily full backup schedule and 30-day archive retention.
- Job retry policy with capped retries (max 3).

## 8. Quality Strategy

- Unit + API test coverage across happy path, edge, and error cases.
- Enforced linting, typing, and test gate via `run_tests.sh`.
- Structured error envelope: `{ code, message, details }`.

## 9. Delivery Plan

- Phase 0: Foundation
- Phase 1: Schema + migrations
- Phase 2: Identity and auth
- Phase 3: RBAC and isolation
- Phase 4: Workflow engine
- Phase 5: Analytics + export
- Phase 6: Data governance
- Phase 7: Security hardening
- Phase 8: Full validation and docs
