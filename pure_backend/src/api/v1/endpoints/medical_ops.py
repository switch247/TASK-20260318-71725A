"""Provide operational advanced search endpoints with pagination controls."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.api.v1.dependencies import get_session, require_permission
from src.schemas.medical_ops import AdvancedSearchRequest
from src.services.medical_ops_service import MedicalOpsService

router = APIRouter(prefix="/operations")


@router.post("/search")
def advanced_search(
    request: AdvancedSearchRequest,
    access: tuple[str, str] = Depends(require_permission("analytics", "read")),
    session: Session = Depends(get_session),
) -> dict[str, object]:
    organization_id, _ = access
    service = MedicalOpsService(session)
    return service.advanced_search(organization_id, request)
