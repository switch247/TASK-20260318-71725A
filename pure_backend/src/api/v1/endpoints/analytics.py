"""Expose analytics, report, and export preview endpoints with masking support."""

import json

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.orm import Session

from src.api.v1.dependencies import get_current_user_id, get_session, require_permission
from src.core.errors import NotFoundError
from src.schemas.analytics import (
    CreateExportTaskRequest,
    CreateReportRequest,
    ExportPreviewRequest,
    MetricsQuery,
)
from src.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics")


@router.post("/dashboard")
def dashboard(
    query: MetricsQuery,
    access: tuple[str, str] = Depends(require_permission("analytics", "read")),
    session: Session = Depends(get_session),
) -> dict[str, object]:
    organization_id, _ = access
    service = AnalyticsService(session)
    return service.get_dashboard_metrics(organization_id, query)


@router.post("/reports")
def create_report(
    request: CreateReportRequest,
    http_request: Request,
    access: tuple[str, str] = Depends(require_permission("analytics", "read")),
    current_user_id: str = Depends(get_current_user_id),
    session: Session = Depends(get_session),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
) -> dict[str, str]:
    organization_id, _ = access
    service = AnalyticsService(session)
    report = service.create_report(
        organization_id,
        current_user_id,
        request,
        trace_id=x_trace_id or http_request.headers.get("X-Trace-Id"),
    )
    return {"id": report.id, "name": report.name}


@router.post("/exports")
def create_export(
    request: CreateExportTaskRequest,
    http_request: Request,
    access: tuple[str, str] = Depends(require_permission("export", "request")),
    current_user_id: str = Depends(get_current_user_id),
    session: Session = Depends(get_session),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
) -> dict[str, str]:
    organization_id, _ = access
    service = AnalyticsService(session)
    task = service.create_export_task(
        organization_id,
        current_user_id,
        request,
        trace_id=x_trace_id or http_request.headers.get("X-Trace-Id"),
    )
    return {"task_id": task.id, "trace_code": task.trace_code, "status": task.status.value}


@router.post("/exports/preview")
def preview_export(
    request: ExportPreviewRequest,
    access: tuple[str, str] = Depends(require_permission("export", "request")),
    session: Session = Depends(get_session),
) -> dict[str, object]:
    _, role_name = access
    service = AnalyticsService(session)

    field_whitelist = json.loads(request.field_whitelist_json)
    desensitization_policy = json.loads(request.desensitization_policy_json)
    rows = [row.values for row in request.rows]

    preview_rows = service.preview_export_rows(
        role_name=role_name,
        field_whitelist=field_whitelist,
        desensitization_policy=desensitization_policy,
        rows=rows,
    )
    return {"items": preview_rows, "count": len(preview_rows)}


@router.post("/exports/{task_id}/execute")
def execute_export(
    task_id: str,
    http_request: Request,
    access: tuple[str, str] = Depends(require_permission("export", "request")),
    current_user_id: str = Depends(get_current_user_id),
    session: Session = Depends(get_session),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
) -> dict[str, object]:
    organization_id, role_name = access
    service = AnalyticsService(session)
    return service.execute_export_task(
        organization_id=organization_id,
        user_id=current_user_id,
        role_name=role_name,
        task_id=task_id,
        trace_id=x_trace_id or http_request.headers.get("X-Trace-Id"),
    )


@router.get("/exports")
def list_exports(
    page: int = 1,
    limit: int = 20,
    access: tuple[str, str] = Depends(require_permission("export", "read")),
    session: Session = Depends(get_session),
) -> dict[str, object]:
    organization_id, _ = access
    service = AnalyticsService(session)
    offset = (page - 1) * limit
    tasks = service.repository.list_export_tasks(organization_id, limit, offset)
    items = [
        {
            "task_id": t.id,
            "resource": t.resource,
            "status": t.status.value,
            "trace_code": t.trace_code,
        }
        for t in tasks
    ]
    return {"items": items, "count": len(items), "page": page, "limit": limit}


@router.get("/exports/{task_id}")
def get_export(
    task_id: str,
    access: tuple[str, str] = Depends(require_permission("export", "read")),
    session: Session = Depends(get_session),
) -> dict[str, object]:
    organization_id, _ = access
    service = AnalyticsService(session)
    task = service.repository.get_export_task(organization_id, task_id)
    if not task:
        raise NotFoundError("Export task not found")
    return {
        "task_id": task.id,
        "resource": task.resource,
        "status": task.status.value,
        "trace_code": task.trace_code,
        "result_path": task.result_path,
    }
