"""Implement secure attachment and immutable audit operations with business ownership checks."""

import base64
import hashlib
import json
from pathlib import Path

from sqlalchemy.orm import Session

from src.core.config import get_settings
from src.core.errors import ForbiddenError, NotFoundError, ValidationError
from src.models.security import Attachment, ImmutableAuditLog, OperationLog
from src.repositories.security_repository import SecurityRepository
from src.services.masking_service import mask_storage_path
from src.services.operation_logger import OperationLogger

settings = get_settings()


class SecurityService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = SecurityRepository(session)
        self.operation_logger = OperationLogger(session)

    def create_attachment(
        self,
        organization_id: str,
        user_id: str,
        process_instance_id: str | None,
        business_number: str | None,
        file_name: str,
        mime_type: str,
        file_size_bytes: int,
        file_content_base64: str,
        trace_id: str | None = None,
    ) -> dict[str, str]:
        if process_instance_id is not None:
            if business_number is None:
                raise ValidationError(
                    "business_number is required when process_instance_id is provided"
                )
            if not self.repository.process_instance_belongs_to_business(
                organization_id,
                process_instance_id,
                business_number,
            ):
                raise ForbiddenError("Attachment business context is invalid")

        max_size_bytes = settings.max_upload_size_mb * 1024 * 1024
        if file_size_bytes > max_size_bytes:
            raise ValidationError("File exceeds maximum allowed size")

        if mime_type not in {
            "application/pdf",
            "image/png",
            "image/jpeg",
            "text/plain",
            "application/json",
        }:
            raise ValidationError("Unsupported file type")

        content = base64.b64decode(file_content_base64.encode("utf-8"), validate=True)
        if len(content) != file_size_bytes:
            raise ValidationError("Declared file size does not match uploaded payload")
        if len(content) > max_size_bytes:
            raise ValidationError("File exceeds maximum allowed size")
        fingerprint = hashlib.sha256(content).hexdigest()
        existing = self.repository.find_attachment_by_fingerprint(organization_id, fingerprint)
        if existing is not None:
            return {
                "attachment_id": existing.id,
                "fingerprint": existing.sha256_fingerprint,
                "deduplicated": "true",
            }

        storage_dir = Path("storage/attachments")
        storage_dir.mkdir(parents=True, exist_ok=True)
        target_path = storage_dir / f"{fingerprint}_{file_name}"
        target_path.write_bytes(content)

        attachment = Attachment(
            organization_id=organization_id,
            process_instance_id=process_instance_id,
            uploader_user_id=user_id,
            file_name=file_name,
            mime_type=mime_type,
            file_size_bytes=file_size_bytes,
            sha256_fingerprint=fingerprint,
            storage_path=str(target_path),
            is_deleted=False,
        )
        self.repository.create_attachment(attachment)
        self._log_operation(
            organization_id=organization_id,
            user_id=user_id,
            action="create",
            resource="attachment",
            resource_id=attachment.id,
            metadata={"file_name": file_name, "fingerprint": fingerprint},
        )
        self.operation_logger.log(
            actor_id=user_id,
            organization_id=organization_id,
            resource_type="attachment",
            resource_id=attachment.id,
            operation="create",
            trace_id=trace_id,
            after={
                "process_instance_id": attachment.process_instance_id,
                "fingerprint": attachment.sha256_fingerprint,
            },
        )
        self.session.commit()
        return {
            "attachment_id": attachment.id,
            "fingerprint": attachment.sha256_fingerprint,
            "deduplicated": "false",
        }

    def get_attachment(
        self,
        organization_id: str,
        attachment_id: str,
        business_number: str,
        role_name: str,
    ) -> dict[str, str | int]:
        attachment = self.repository.get_attachment(attachment_id)
        if attachment is None or attachment.is_deleted:
            raise NotFoundError("Attachment not found")
        if attachment.organization_id != organization_id:
            raise ForbiddenError("Attachment does not belong to organization")
        if attachment.process_instance_id is not None:
            if not self.repository.process_instance_belongs_to_business(
                organization_id,
                attachment.process_instance_id,
                business_number,
            ):
                raise ForbiddenError("Attachment does not belong to provided business context")

        return {
            "id": attachment.id,
            "file_name": attachment.file_name,
            "mime_type": attachment.mime_type,
            "file_size_bytes": attachment.file_size_bytes,
            "storage_path": mask_storage_path(attachment.storage_path, role_name),
        }

    def append_immutable_audit(
        self,
        organization_id: str,
        user_id: str,
        event_type: str,
        event_payload_json: str,
        trace_id: str | None = None,
    ) -> dict[str, str]:
        payload_obj = json.loads(event_payload_json)
        latest = self.repository.latest_audit_log()
        previous_hash = latest.current_hash if latest is not None else ""
        raw_material = f"{previous_hash}|{event_type}|{json.dumps(payload_obj, sort_keys=True)}"
        current_hash = hashlib.sha256(raw_material.encode("utf-8")).hexdigest()

        log = ImmutableAuditLog(
            organization_id=organization_id,
            actor_user_id=user_id,
            event_type=event_type,
            event_payload_json=event_payload_json,
            previous_hash=previous_hash or None,
            current_hash=current_hash,
        )
        self.repository.create_immutable_audit_log(log)
        self.operation_logger.log(
            actor_id=user_id,
            organization_id=organization_id,
            resource_type="immutable_audit",
            resource_id=log.id,
            operation="append",
            trace_id=trace_id,
            after={"event_type": event_type, "current_hash": current_hash},
        )
        self.session.commit()
        return {"audit_id": log.id, "current_hash": log.current_hash}

    def _log_operation(
        self,
        organization_id: str,
        user_id: str,
        action: str,
        resource: str,
        resource_id: str,
        metadata: dict[str, object],
    ) -> None:
        self.repository.create_operation_log(
            OperationLog(
                organization_id=organization_id,
                actor_user_id=user_id,
                action=action,
                resource=resource,
                resource_id=resource_id,
                request_id=None,
                metadata_json=json.dumps(metadata),
            )
        )
