"""Expose secure attachment and audit endpoints with trace-aware mutation hooks."""

from fastapi import APIRouter, Depends, Header, Query, Request
from sqlalchemy.orm import Session

from src.api.v1.dependencies import get_current_user_id, get_session, require_permission
from src.schemas.security import AuditEventRequest, CreateAttachmentRequest
from src.services.security_service import SecurityService

router = APIRouter(prefix="/security")


@router.post("/attachments")
def create_attachment(
    request: CreateAttachmentRequest,
    http_request: Request,
    access: tuple[str, str] = Depends(require_permission("process", "create")),
    current_user_id: str = Depends(get_current_user_id),
    session: Session = Depends(get_session),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
) -> dict[str, str]:
    organization_id, _ = access
    service = SecurityService(session)
    return service.create_attachment(
        organization_id=organization_id,
        user_id=current_user_id,
        process_instance_id=request.process_instance_id,
        business_number=request.business_number,
        file_name=request.file_name,
        mime_type=request.mime_type,
        file_size_bytes=request.file_size_bytes,
        file_content_base64=request.file_content_base64,
        trace_id=x_trace_id or http_request.headers.get("X-Trace-Id"),
    )


@router.get("/attachments/{attachment_id}")
def get_attachment(
    attachment_id: str,
    business_number: str = Query(min_length=1),
    access: tuple[str, str] = Depends(require_permission("process", "review")),
    session: Session = Depends(get_session),
) -> dict[str, str | int]:
    organization_id, role_name = access
    service = SecurityService(session)
    return service.get_attachment(organization_id, attachment_id, business_number, role_name)


@router.post("/audit/append")
def append_audit(
    request: AuditEventRequest,
    http_request: Request,
    access: tuple[str, str] = Depends(require_permission("audit", "append")),
    current_user_id: str = Depends(get_current_user_id),
    session: Session = Depends(get_session),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
) -> dict[str, str]:
    organization_id, _ = access
    service = SecurityService(session)
    return service.append_immutable_audit(
        organization_id=organization_id,
        user_id=current_user_id,
        event_type=request.event_type,
        event_payload_json=request.event_payload_json,
        trace_id=x_trace_id or http_request.headers.get("X-Trace-Id"),
    )


@router.get("/audit/verify")
def verify_audit(
    access: tuple[str, str] = Depends(require_permission("audit", "read")),
    session: Session = Depends(get_session),
) -> dict[str, object]:
    from src.services.operation_logger import OperationLogger

    service = OperationLogger(session)
    return service.verify_integrity()

