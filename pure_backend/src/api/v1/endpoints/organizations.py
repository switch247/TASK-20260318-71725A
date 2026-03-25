from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.api.v1.dependencies import get_current_user_id, get_session
from src.schemas.organization import (
    CreateOrganizationRequest,
    JoinOrganizationRequest,
    OrganizationResponse,
)
from src.services.auth_service import AuthService

router = APIRouter(prefix="/organizations")


@router.post("", response_model=OrganizationResponse)
def create_organization(
    request: CreateOrganizationRequest,
    current_user_id: str = Depends(get_current_user_id),
    session: Session = Depends(get_session),
) -> OrganizationResponse:
    service = AuthService(session)
    organization = service.create_organization(request, current_user_id)
    return OrganizationResponse(id=organization.id, code=organization.code, name=organization.name)


@router.post("/join")
def join_organization(
    request: JoinOrganizationRequest,
    current_user_id: str = Depends(get_current_user_id),
    session: Session = Depends(get_session),
) -> dict[str, bool]:
    service = AuthService(session)
    service.join_organization(request, current_user_id)
    return {"success": True}
