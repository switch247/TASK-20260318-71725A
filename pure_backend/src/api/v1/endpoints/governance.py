"""Expose governance APIs for snapshots, rollback, and maintenance job execution."""

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.orm import Session

from src.api.v1.dependencies import get_current_user_id, get_session, require_permission
from src.schemas.governance import (
    CreateImportBatchRequest,
    CreateSnapshotRequest,
    RollbackSnapshotRequest,
)
from src.services.governance_service import GovernanceService

router = APIRouter(prefix="/governance")


@router.post("/imports")
def create_import_batch(
    request: CreateImportBatchRequest,
    http_request: Request,
    access: tuple[str, str] = Depends(require_permission("governance", "manage")),
    current_user_id: str = Depends(get_current_user_id),
    session: Session = Depends(get_session),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
) -> dict[str, object]:
    organization_id, _ = access
    service = GovernanceService(session)
    return service.create_import_batch(
        organization_id,
        current_user_id,
        request,
        trace_id=x_trace_id or http_request.headers.get("X-Trace-Id"),
    )


@router.post("/snapshots")
def create_snapshot(
    request: CreateSnapshotRequest,
    http_request: Request,
    access: tuple[str, str] = Depends(require_permission("governance", "manage")),
    session: Session = Depends(get_session),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
) -> dict[str, str | int]:
    organization_id, _ = access
    service = GovernanceService(session)
    return service.create_snapshot(
        organization_id,
        request,
        trace_id=x_trace_id or http_request.headers.get("X-Trace-Id"),
    )


@router.post("/snapshots/rollback")
def rollback_snapshot(
    request: RollbackSnapshotRequest,
    http_request: Request,
    access: tuple[str, str] = Depends(require_permission("governance", "manage")),
    session: Session = Depends(get_session),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
) -> dict[str, str]:
    organization_id, _ = access
    service = GovernanceService(session)
    return service.rollback_snapshot(
        organization_id,
        request.snapshot_id,
        trace_id=x_trace_id or http_request.headers.get("X-Trace-Id"),
    )


@router.post("/jobs/bootstrap")
def bootstrap_jobs(
    http_request: Request,
    _: tuple[str, str] = Depends(require_permission("governance", "manage")),
    session: Session = Depends(get_session),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
) -> dict[str, list[dict[str, object]]]:
    service = GovernanceService(session)
    return {
        "jobs": service.schedule_maintenance_jobs(
            trace_id=x_trace_id or http_request.headers.get("X-Trace-Id")
        )
    }


@router.post("/jobs/execute")
def execute_jobs(
    http_request: Request,
    _: tuple[str, str] = Depends(require_permission("governance", "manage")),
    session: Session = Depends(get_session),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
) -> dict[str, object]:
    service = GovernanceService(session)
    return service.execute_due_jobs(trace_id=x_trace_id or http_request.headers.get("X-Trace-Id"))


@router.get("/snapshots")
def list_snapshots(
    domain: str,
    page: int = 1,
    limit: int = 20,
    access: tuple[str, str] = Depends(require_permission("governance", "manage")),
    session: Session = Depends(get_session),
) -> dict[str, object]:
    organization_id, _ = access
    service = GovernanceService(session)
    snapshots = service.repository.list_snapshots(organization_id, domain)
    start = (page - 1) * limit
    end = start + limit
    items = snapshots[start:end]
    return {
        "count": len(items),
        "total_count": len(snapshots),
        "page": page,
        "limit": limit,
        "items": [
            {"snapshot_id": item.id, "domain": item.domain, "version": item.version}
            for item in items
        ],
    }
