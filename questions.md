1. Question: Who can create organizations?
	Understanding: It's unclear whether organization creation is privileged (Admins/Super Admins) or available to any registered user. This decision affects onboarding flows, invitations, and quotas.
	Solution: Specify one of:
	- Admin-only creation: only `admin` or `super_admin` roles can create orgs; onboarding requires an invite.
	- Self-serve creation: any registered user can create an org and becomes its initial admin; enforce rate limits and an approval workflow if needed.
	Implement the chosen policy in the organization service and API validation layer.

2. Question: Organization codes uniqueness scope?
	Understanding: Need to know whether `organization.code` must be globally unique or unique within some scope; this affects DB constraints and lookups.
	Solution: Require global uniqueness (unique DB index) unless a scoped uniqueness model is explicitly needed; document the constraint and migration plan.

3. Question: Idempotent key window for approvals?
	Understanding: Requirements mention a 24-hour dedupe window keyed by a business identifier; unclear handling for retries or near-duplicates.
	Solution: Define policy:
	- Store an idempotency key composed of (operation_type, business_number) with a 24h TTL.
	- Duplicate requests within 24h return the original result; after 24h, allow a new operation.
	- Provide an admin override for forced retries and document HTTP semantics (409 vs 200 with same response id).

4. Question: SLA enforcement vs reminders?
	Understanding: Default SLA is 48 hours; clarify reminder schedule and actions on breach (escalation, auto-close, or audit-only).
	Solution: Specify reminder times (e.g., at 24h and 12h remaining), escalation steps (notify manager, create task), and breach behavior (mark overdue, escalate to admin). Implement reminders via scheduled jobs and surface SLA state in entity attributes.

5. Question: Attachment ownership validation rules?
	Understanding: Clarify whether attachments inherit ownership from parent records or store explicit owner metadata; this affects ACL checks and transfer behavior.
	Solution: Store explicit `owner_id` and `owner_type` (or `organization_id`) on attachments and validate access by checking both attachment owner and parent ownership when necessary. If inheritance is used, ensure efficient parent lookups.

6. Question: Export desensitization per role?
	Understanding: Exports should apply the same field-level masking rules as API responses, but auditor or compliance roles may need unmasked exports.
	Solution: Define a masking matrix mapping roles to field visibility and implement masking at serialization/export time. Add an approval path for full-data exports and log export actions.

7. Question: Backup and archive retention details?
	Understanding: Notes mention daily backups and 30-day archiving, but retention, restore windows, and restore procedures are unspecified.
	Solution: Specify backup cadence (daily full, hourly incremental), retention windows for backups vs archives, restore SLAs, and test/verify restore procedures. Document storage location and access controls.

8. Question: Password rules and recovery flow?
	Understanding: Password recovery must be a password reset (not account reveal) and can be performed by an Admin. External integrations (email, SMS/OTP) are not permitted currently.
	Solution: Define a password reset flow supporting:
	- Admin-initiated reset: Admin triggers a reset forcing user to set a new password at next login.
	- Limited user-initiated requests: Until external integrations are enabled, user requests route to admins or an internal support flow.
	- Security: Enforce minimum password length (≥8) and composition (letters + numbers); consider future passphrase or complexity rules.
	- Tokens: If reset tokens are later introduced, enforce single-use and short expiry (e.g., 1 hour).
	- Audit: Log all reset actions (actor, target, timestamp, reason).

9. Question: Audit log immutability scope?
	Understanding: Assume critical actions are written immutably; confirm action coverage and retention/access policies.
	Solution: Define audit scope (auth events, role changes, exports, password resets, data changes). Use append-only storage or immutability guarantees, and define retention and access controls for auditors.

10. Question: User lockout timing and reset?
	 Understanding: Described rule: 5 failed attempts within 10 minutes -> 30-minute lockout; unclear if lockout is per account, IP, or org.
	 Solution: Recommend per-account lockout with optional IP rate-limiting. Provide admin unlock and automatic unlock after the lockout interval. Log lockouts for audit.

11. Question: Data versioning granularity?
	 Understanding: System supports snapshots/rollbacks and lineage but does not specify which entities are versioned or the scope (record vs dataset).
	 Solution: Decide between per-record versioning for critical entities and periodic dataset snapshots. Implement history APIs and document retention/size tradeoffs.

12. Question: Role model details and admin scope?
	 Understanding: Roles listed: `admin`, `reviewer`, `general`, `auditor` — default permissions and cross-org admin capabilities are unspecified.
	 Solution: Produce a role-permissions matrix and define whether `admin` is global or org-scoped. If needed, add a `scope` attribute to roles to restrict assignment.

13. Question: Parallel/joint signing behavior?
	 Understanding: Workflows support parallel/joint signing; unspecified whether all signers are required or a quorum suffices.
	 Solution: Allow workflow configuration for completion policy: `all_required` or `quorum:N`. Implement status tracking and notify participants when threshold is reached.

14. Question: Idempotency keys storage and expiry?
	 Understanding: Idempotency keys dedupe approvals for 24 hours; storage and enforcement details are not defined.
	 Solution: Persist idempotency keys in a durable store (DB unique index or Redis with TTL) and ensure atomic check-and-set semantics. On collision, return prior result and log event.

15. Question: Sensitive field encryption at rest?
	 Understanding: PII (ID numbers, contact details) should be encrypted; unclear if DB-level or application-level encryption is desired.
	 Solution: Prefer application-level field encryption with KMS-managed keys for sensitive fields. Document deterministic vs non-deterministic encryption needs and key rotation procedures.

16. Question: Multi-criteria search filters exposure?
	 Understanding: Advanced filters exist, but which fields are permitted for which roles is unclear (privacy concerns).
	 Solution: Create a searchable-fields registry with visibility tags (`public`, `restricted`, `private`) and enforce field visibility in the search API. Add rate limits and audit export queries.

17. Question: Export traceability requirements?
	 Understanding: Exports must be auditable; need to capture who exported data and the filters used.
	 Solution: Log exports with `actor_id`, `actor_role`, `timestamp`, `entity`, `filters`, `fields`, `record_count`, and `destination`. Store export logs immutably and provide an audit view.

18. Question: Attachment deduplication fingerprint?
	 Understanding: Attachments are deduped by fingerprint; collision handling and algorithm are unspecified.
	 Solution: Use SHA-256 for fingerprinting, record size+fingerprint, and on collision verify bytes before deduping. Maintain reference counts and GC for orphaned files.

19. Question: Transaction consistency during workflows?
	 Understanding: Uses SQLAlchemy/Postgres; unclear isolation level and approach for long-running workflows.
	 Solution: Use short DB transactions and persist workflow state/events to enable resumable steps. Avoid long-running DB transactions; employ saga/compensation patterns for multi-step operations.

20. Question: Daily tasks retry policy specifics?
	 Understanding: Scheduled jobs should retry on failure; backoff and alerting are unspecified.
	 Solution: Adopt exponential backoff (e.g., 1m, 5m, 15m) with a max of 3 retries, and send alerts on final failure. Log retry attempts and error details for diagnostics.
