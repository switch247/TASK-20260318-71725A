from sqlalchemy import event
from src.core.errors import ValidationError
from src.models.security import OperationLog, ImmutableAuditLog

def block_log_mutation(mapper, connection, target):
    raise ValidationError("Mutation (UPDATE/DELETE) not allowed on immutable audit tables")

def enforce_audit_immutability():
    """Register SQLAlchemy listeners to block updates and deletes on log tables."""
    for model in [OperationLog, ImmutableAuditLog]:
        event.listen(model, "before_update", block_log_mutation)
        event.listen(model, "before_delete", block_log_mutation)
