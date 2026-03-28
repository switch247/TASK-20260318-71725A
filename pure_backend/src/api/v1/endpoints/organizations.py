from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from src.api.v1.dependencies import get_current_user_id, get_session
from src.schemas.organization import (
    CreateOrganizationRequest,
    JoinOrganizationRequest,
    OrganizationResponse,
)
from src.services.organization_service import OrganizationService

router = APIRouter(prefix="/organizations")


@router.post("", response_model=OrganizationResponse)
def create_organization(
    request: CreateOrganizationRequest,
    http_request: Request,
    current_user_id: str = Depends(get_current_user_id),
    session: Session = Depends(get_session),
) -> OrganizationResponse:
    service = OrganizationService(session)
    organization = service.create_organization(
        request,
        current_user_id,
        trace_id=http_request.headers.get("X-Trace-Id"),
    )
    return OrganizationResponse(id=organization.id, code=organization.code, name=organization.name)


@router.post("/join")
def join_organization(
    request: JoinOrganizationRequest,
    http_request: Request,
    current_user_id: str = Depends(get_current_user_id),
    session: Session = Depends(get_session),
) -> dict[str, bool]:
    service = OrganizationService(session)
    service.join_organization(
        request,
        current_user_id,
        trace_id=http_request.headers.get("X-Trace-Id"),
    )
    return {"success": True}
