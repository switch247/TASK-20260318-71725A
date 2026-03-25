"""Expose analytics, report, and export preview endpoints with masking support."""

import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.api.v1.dependencies import get_current_user_id, get_session, require_permission
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
    access: tuple[str, str] = Depends(require_permission("analytics", "read")),
    current_user_id: str = Depends(get_current_user_id),
    session: Session = Depends(get_session),
) -> dict[str, str]:
    organization_id, _ = access
    service = AnalyticsService(session)
    report = service.create_report(organization_id, current_user_id, request)
    return {"id": report.id, "name": report.name}


@router.post("/exports")
def create_export(
    request: CreateExportTaskRequest,
    access: tuple[str, str] = Depends(require_permission("export", "request")),
    current_user_id: str = Depends(get_current_user_id),
    session: Session = Depends(get_session),
) -> dict[str, str]:
    organization_id, _ = access
    service = AnalyticsService(session)
    task = service.create_export_task(organization_id, current_user_id, request)
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
