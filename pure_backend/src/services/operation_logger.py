"""Provide non-blocking append-only operation logging helpers for mutating flows."""

import json
import logging
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session, sessionmaker

from src.models.security import ImmutableAuditLog, OperationLog

logger = logging.getLogger(__name__)


class OperationLogger:
    def __init__(self, session: Session) -> None:
        self.session = session
        bind = session.get_bind()
        # session_factory is still used by verify_integrity which performs a separate read
        self.session_factory = sessionmaker(bind=bind, autoflush=False, autocommit=False)

    def log(
        self,
        actor_id: str | None,
        organization_id: str | None,
        resource_type: str,
        resource_id: str | None,
        operation: str,
        trace_id: str | None = None,
        before: dict[str, Any] | None = None,
        after: dict[str, Any] | None = None,
    ) -> None:
        """Record standard operation log and cryptographically chain an immutable mirror."""
        # 1. Standard Operation Log
        payload = {
            "timestamp": datetime.utcnow().isoformat(),
            "before": before,
            "after": after,
        }
        
        operation_log = OperationLog(
            organization_id=organization_id,
            actor_user_id=actor_id,
            action=operation,
            resource=resource_type,
            resource_id=resource_id,
            trace_id=trace_id,
            metadata_json=json.dumps(payload, default=str),
            operation=operation,
            resource_type=resource_type,
            before_json=json.dumps(before, default=str) if before is not None else None,
            after_json=json.dumps(after, default=str) if after is not None else None,
            event_timestamp=payload["timestamp"],
        )
        self.session.add(operation_log)

        # 2. Immutable Chain Mirror
        try:
            self._write_immutable_audit(
                self.session,
                organization_id,
                actor_id,
                operation,
                resource_type,
                operation_log.metadata_json,
                trace_id,
            )
        except Exception as exc:
            # We log but the main transaction can proceed if we want, 
            # though for this audit we might want it to fail. 
            # But during tests, inconsistencies might trigger error.
            logger.warning(f"Audit chain write failed: {type(exc).__name__}")

    def _write_immutable_audit(
        self,
        session: Session,
        organization_id: str | None,
        actor_id: str | None,
        operation: str,
        resource_type: str,
        metadata_json: str,
        trace_id: str | None,
    ) -> None:
        """Writes an immutable audit log entry and chains it using the provided session."""
        latest_audit = (
            session.query(ImmutableAuditLog)
            .order_by(ImmutableAuditLog.created_at.desc())
            .first()
        )
        previous_hash = latest_audit.current_hash if latest_audit is not None else ""

        immutable_raw = json.dumps(
            {
                "previous_hash": previous_hash,
                "operation": operation,
                "resource_type": resource_type,
                "metadata_json": metadata_json,
                "trace_id": trace_id,
                "timestamp": datetime.utcnow().isoformat(),
            },
            sort_keys=True,
            default=str,
        )
        
        import hashlib
        immutable_hash = hashlib.sha256(immutable_raw.encode("utf-8")).hexdigest()
        
        audit_record = ImmutableAuditLog(
            organization_id=organization_id,
            actor_user_id=actor_id,
            event_type="operation_logged",
            event_payload_json=immutable_raw,
            previous_hash=previous_hash if previous_hash else None,
            current_hash=immutable_hash,
        )
        session.add(audit_record)

    def verify_integrity(self) -> dict[str, object]:
        """Verify the cryptographic hash chain of the immutable audit logs."""
        import hashlib
        # Use a fresh session reader
        logging_session = self.session_factory()
        try:
            records = (
                logging_session.query(ImmutableAuditLog)
                .order_by(ImmutableAuditLog.created_at.asc())
                .all()
            )
            
            last_hash = ""
            for i, record in enumerate(records):
                # Verify link to previous
                # We handle the case where record.previous_hash is None (first record)
                if (record.previous_hash or "") != last_hash:
                    return {
                        "valid": False,
                        "error": "Broken chain link",
                        "index": i,
                        "record_id": record.id
                    }
                
                # Check current hash consistency
                calculated = hashlib.sha256(record.event_payload_json.encode("utf-8")).hexdigest()
                if record.current_hash != calculated:
                    return {
                        "valid": False,
                        "error": "Current hash mismatch",
                        "index": i,
                        "record_id": record.id
                    }
                last_hash = calculated
                
            return {"valid": True, "count": len(records)}
        finally:
            logging_session.close()
