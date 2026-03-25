from fastapi import APIRouter, Depends
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
    access: tuple[str, str] = Depends(require_permission("governance", "manage")),
    current_user_id: str = Depends(get_current_user_id),
    session: Session = Depends(get_session),
) -> dict[str, object]:
    organization_id, _ = access
    service = GovernanceService(session)
    return service.create_import_batch(organization_id, current_user_id, request)


@router.post("/snapshots")
def create_snapshot(
    request: CreateSnapshotRequest,
    access: tuple[str, str] = Depends(require_permission("governance", "manage")),
    session: Session = Depends(get_session),
) -> dict[str, str | int]:
    organization_id, _ = access
    service = GovernanceService(session)
    return service.create_snapshot(organization_id, request)


@router.post("/snapshots/rollback")
def rollback_snapshot(
    request: RollbackSnapshotRequest,
    access: tuple[str, str] = Depends(require_permission("governance", "manage")),
    session: Session = Depends(get_session),
) -> dict[str, str]:
    organization_id, _ = access
    service = GovernanceService(session)
    return service.rollback_snapshot(organization_id, request.snapshot_id)


@router.post("/jobs/bootstrap")
def bootstrap_jobs(
    _: tuple[str, str] = Depends(require_permission("governance", "manage")),
    session: Session = Depends(get_session),
) -> dict[str, list[dict[str, object]]]:
    service = GovernanceService(session)
    return {"jobs": service.schedule_maintenance_jobs()}
