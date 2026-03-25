# Architecture Notes

## Layering

- **API**: FastAPI endpoints and dependency wiring.
- **Services**: Business rules and transaction boundaries.
- **Repositories**: SQLAlchemy query implementations.
- **Models**: Domain persistence schema.

## Core Domains

- Identity and organization
- Authorization and permissions
- Process/workflow management
- Operations analytics and export
- Data governance and quality
- Security/compliance and auditing

## Data Isolation

Organization id is enforced as a first-class boundary and checked before privileged operations.

## Compliance Features

- Login lockout control (5 failures in 10 minutes, 30-minute lock)
- Sensitive field encryption utilities
- File upload size/type constraints and dedup fingerprinting
- Immutable audit chain with hash linking
- HTTPS enforcement middleware for API routes
- Business-level attachment ownership authorization (`organization + business_number`)
- Workflow execution supports conditional nodes and parallel/joint flags
- Export preview applies field whitelist and role-based desensitization

## Reliability

- Domain errors use consistent envelope and status mapping.
- Job records support retry and fault compensation tracking.
- Test and static analysis gates are integrated early in the build.
