from datetime import datetime, UTC

from src.services.operation_logger import OperationLogger
from src.models.security import OperationLog


def test_operation_log_redacts_sensitive_fields(db_session):
    logger = OperationLogger(db_session)

    before = {"username": "alice", "password": "hunter2", "nested": {"token": "t-123"}}
    # use longer, unique secret values to avoid accidental substring matches
    secret_value = "secret-xyz-123"
    after = {"status": "updated", "access_token": "a-456", "list": [{"secret": secret_value}]}

    # Use None for actor_id and organization_id so foreign key constraints do not fail
    logger.log(actor_id=None, organization_id=None, resource_type="test", resource_id="r1", operation="update", trace_id=None, before=before, after=after)
    db_session.commit()

    rec = db_session.query(OperationLog).order_by(OperationLog.created_at.desc()).first()
    assert rec is not None

    before_json = rec.before_json
    after_json = rec.after_json

    assert "hunter2" not in (before_json or "")
    assert "t-123" not in (before_json or "")
    assert "a-456" not in (after_json or "")
    assert secret_value not in (after_json or "")
