# Architecture Notes

Layers:

- API: request validation, dependency injection, HTTP contracts
- Service: business rules and transactional orchestration
- Repository: query and persistence operations
- Models: SQLAlchemy entities and constraints

Cross-cutting concerns:

- JWT auth + org membership enforcement
- RBAC permission checks
- HTTPS enforcement middleware
- Operation logging + immutable audit chaining
- Role-based response masking
