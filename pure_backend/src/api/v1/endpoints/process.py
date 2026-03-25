"""Expose process domain APIs including reminders and trace-aware mutation calls."""

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.orm import Session

from src.api.v1.dependencies import get_current_user_id, get_session, require_permission
from src.schemas.process import (
    CreateProcessDefinitionRequest,
    DecideTaskRequest,
    ProcessInstanceResponse,
    ReminderDispatchResponse,
    SubmitProcessRequest,
)
from src.services.process_service import ProcessService

router = APIRouter(prefix="/process")


@router.post("/definitions")
def create_definition(
    request: CreateProcessDefinitionRequest,
    http_request: Request,
    access: tuple[str, str] = Depends(require_permission("process", "manage")),
    session: Session = Depends(get_session),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
) -> dict[str, str]:
    organization_id, _ = access
    service = ProcessService(session)
    definition = service.create_definition(
        organization_id,
        request,
        trace_id=x_trace_id or http_request.headers.get("X-Trace-Id"),
    )
    return {"id": definition.id, "name": definition.name}


@router.post("/instances", response_model=ProcessInstanceResponse)
def submit_instance(
    request: SubmitProcessRequest,
    http_request: Request,
    access: tuple[str, str] = Depends(require_permission("process", "create")),
    current_user_id: str = Depends(get_current_user_id),
    session: Session = Depends(get_session),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
) -> ProcessInstanceResponse:
    organization_id, _ = access
    service = ProcessService(session)
    return service.submit_process(
        organization_id,
        current_user_id,
        request,
        trace_id=x_trace_id or http_request.headers.get("X-Trace-Id"),
    )


@router.get("/tasks/pending")
def list_pending_tasks(
    access: tuple[str, str] = Depends(require_permission("process", "review")),
    current_user_id: str = Depends(get_current_user_id),
    session: Session = Depends(get_session),
) -> dict[str, list[dict[str, str]]]:
    organization_id, _ = access
    service = ProcessService(session)
    return {"items": service.list_pending_tasks(organization_id, current_user_id)}


@router.post("/tasks/decision")
def decide_task(
    request: DecideTaskRequest,
    http_request: Request,
    access: tuple[str, str] = Depends(require_permission("process", "review")),
    current_user_id: str = Depends(get_current_user_id),
    session: Session = Depends(get_session),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
) -> dict[str, str]:
    organization_id, _ = access
    service = ProcessService(session)
    return service.decide_task(
        organization_id,
        current_user_id,
        request,
        trace_id=x_trace_id or http_request.headers.get("X-Trace-Id"),
    )


@router.post("/reminders/dispatch", response_model=ReminderDispatchResponse)
def dispatch_sla_reminders(
    http_request: Request,
    access: tuple[str, str] = Depends(require_permission("process", "manage")),
    session: Session = Depends(get_session),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
) -> ReminderDispatchResponse:
    organization_id, _ = access
    service = ProcessService(session)
    return service.dispatch_sla_reminders(
        organization_id,
        trace_id=x_trace_id or http_request.headers.get("X-Trace-Id"),
    )
