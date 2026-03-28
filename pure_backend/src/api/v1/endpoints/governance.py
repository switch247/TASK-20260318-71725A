"""Expose governance APIs for snapshots, rollback, and maintenance job execution."""

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from src.api.v1.dependencies import get_current_user_id, get_session, require_permission
from src.schemas.governance import (
    CreateImportBatchRequest,
    CreateSnapshotRequest,
    DataDictionaryCreate,
    DataDictionaryResponse,
    DataDictionaryUpdate,
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
    access: tuple[str, str] = Depends(require_permission("governance", "manage")),
    session: Session = Depends(get_session),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
) -> dict[str, list[dict[str, object]]]:
    organization_id, _ = access
    service = GovernanceService(session)
    return {
        "jobs": service.schedule_maintenance_jobs(
            organization_id, trace_id=x_trace_id or http_request.headers.get("X-Trace-Id")
        )
    }


@router.post("/jobs/execute")
def execute_jobs(
    http_request: Request,
    access: tuple[str, str] = Depends(require_permission("governance", "manage")),
    session: Session = Depends(get_session),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
) -> dict[str, object]:
    organization_id, _ = access
    service = GovernanceService(session)
    return service.execute_due_jobs(
        organization_id, trace_id=x_trace_id or http_request.headers.get("X-Trace-Id")
    )


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


@router.get("/data-dictionaries")
def list_data_dictionaries(
    domain: str | None = None,
    access: tuple[str, str] = Depends(require_permission("governance", "manage")),
    session: Session = Depends(get_session),
) -> list[DataDictionaryResponse]:
    organization_id, _ = access
    service = GovernanceService(session)
    dds = service.repository.get_data_dictionaries(organization_id, domain)
    return [DataDictionaryResponse.model_validate(dd) for dd in dds]


@router.post("/data-dictionaries")
def create_data_dictionary(
    request: DataDictionaryCreate,
    access: tuple[str, str] = Depends(require_permission("governance", "manage")),
    session: Session = Depends(get_session),
) -> DataDictionaryResponse:
    from src.models.governance import DataDictionary
    organization_id, _ = access
    dd = DataDictionary(
        organization_id=organization_id,
        domain=request.domain,
        code=request.code,
        label=request.label,
        constraints_json=request.constraints_json,
    )
    service = GovernanceService(session)
    created = service.repository.create_data_dictionary(dd)
    return DataDictionaryResponse.model_validate(created)


@router.get("/data-dictionaries/{dd_id}")
def get_data_dictionary(
    dd_id: str,
    access: tuple[str, str] = Depends(require_permission("governance", "manage")),
    session: Session = Depends(get_session),
) -> DataDictionaryResponse:
    organization_id, _ = access
    service = GovernanceService(session)
    dd = service.repository.get_data_dictionary(organization_id, dd_id)
    if not dd:
        raise HTTPException(status_code=404, detail="Data dictionary not found")
    return DataDictionaryResponse.model_validate(dd)


@router.put("/data-dictionaries/{dd_id}")
def update_data_dictionary(
    dd_id: str,
    request: DataDictionaryUpdate,
    access: tuple[str, str] = Depends(require_permission("governance", "manage")),
    session: Session = Depends(get_session),
) -> DataDictionaryResponse:
    organization_id, _ = access
    service = GovernanceService(session)
    dd = service.repository.get_data_dictionary(organization_id, dd_id)
    if not dd:
        raise HTTPException(status_code=404, detail="Data dictionary not found")
    if request.label is not None:
        dd.label = request.label
    if request.constraints_json is not None:
        dd.constraints_json = request.constraints_json
    updated = service.repository.update_data_dictionary(dd)
    return DataDictionaryResponse.model_validate(updated)


@router.delete("/data-dictionaries/{dd_id}")
def delete_data_dictionary(
    dd_id: str,
    access: tuple[str, str] = Depends(require_permission("governance", "manage")),
    session: Session = Depends(get_session),
) -> dict[str, str]:
    organization_id, _ = access
    service = GovernanceService(session)
    dd = service.repository.get_data_dictionary(organization_id, dd_id)
    if not dd:
        raise HTTPException(status_code=404, detail="Data dictionary not found")
    service.repository.delete_data_dictionary(dd)
    return {"message": "Data dictionary deleted"}
