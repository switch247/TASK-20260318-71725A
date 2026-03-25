"""Provide non-blocking append-only operation logging helpers for mutating flows."""

import json
import logging
from datetime import datetime

from sqlalchemy.orm import Session, sessionmaker

from src.models.security import ImmutableAuditLog
from src.models.security import OperationLog

logger = logging.getLogger(__name__)


class OperationLogger:
    def __init__(self, session: Session) -> None:
        bind = session.get_bind()
        self.session_factory = sessionmaker(bind=bind, autoflush=False, autocommit=False)

    def log(
        self,
        *,
        actor_id: str | None,
        organization_id: str | None,
        resource_type: str,
        resource_id: str | None,
        operation: str,
        trace_id: str | None,
        before: dict[str, object] | None = None,
        after: dict[str, object] | None = None,
    ) -> None:
        payload = {
            "timestamp": datetime.utcnow().isoformat(),
            "before": before,
            "after": after,
        }

        try:
            logging_session = self.session_factory()
            try:
                latest_audit = (
                    logging_session.query(ImmutableAuditLog)
                    .order_by(ImmutableAuditLog.created_at.desc())
                    .first()
                )
                previous_hash = latest_audit.current_hash if latest_audit is not None else ""
                logging_session.add(
                    OperationLog(
                        organization_id=organization_id,
                        actor_user_id=actor_id,
                        action=operation,
                        resource=resource_type,
                        resource_id=resource_id,
                        request_id=trace_id,
                        metadata_json=json.dumps(payload, default=str),
                        operation=operation,
                        resource_type=resource_type,
                        trace_id=trace_id,
                        before_json=json.dumps(before, default=str) if before is not None else None,
                        after_json=json.dumps(after, default=str) if after is not None else None,
                        event_timestamp=payload["timestamp"],
                    )
                )
                immutable_raw = json.dumps(
                    {
                        "previous_hash": previous_hash,
                        "operation": operation,
                        "resource_type": resource_type,
                        "resource_id": resource_id,
                        "before": before,
                        "after": after,
                        "trace_id": trace_id,
                        "timestamp": payload["timestamp"],
                    },
                    sort_keys=True,
                    default=str,
                )
                immutable_hash = __import__("hashlib").sha256(immutable_raw.encode("utf-8")).hexdigest()
                logging_session.add(
                    ImmutableAuditLog(
                        organization_id=organization_id,
                        actor_user_id=actor_id,
                        event_type="operation_logged",
                        event_payload_json=immutable_raw,
                        previous_hash=previous_hash or None,
                        current_hash=immutable_hash,
                    )
                )
                logging_session.commit()
            finally:
                logging_session.close()
        except Exception as exc:
            logger.warning("Operation log write failed", extra={"error": str(exc)})
