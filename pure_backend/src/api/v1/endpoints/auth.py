from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from src.api.v1.dependencies import get_current_user_id, get_session
from src.core.errors import NotFoundError
from src.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    PasswordResetRequest,
    RefreshRequest,
    RegisterRequest,
    TokenPairResponse,
)
from src.schemas.user import UserProfileResponse
from src.services.auth_service import AuthService

router = APIRouter(prefix="/auth")


@router.post("/register", response_model=UserProfileResponse)
def register(
    request: RegisterRequest, session: Session = Depends(get_session)
) -> UserProfileResponse:
    service = AuthService(session)
    user = service.register_user(request)
    return UserProfileResponse(
        id=user.id,
        username=user.username,
        display_name=user.display_name,
        email=user.email,
    )


@router.post("/login", response_model=TokenPairResponse)
def login(
    request: LoginRequest,
    session: Session = Depends(get_session),
    user_agent: str | None = Header(default=None),
    x_forwarded_for: str | None = Header(default=None),
) -> TokenPairResponse:
    service = AuthService(session)
    return service.login_user(request, user_agent=user_agent, ip_address=x_forwarded_for)


@router.post("/refresh", response_model=TokenPairResponse)
def refresh(
    request: RefreshRequest,
    session: Session = Depends(get_session),
    user_agent: str | None = Header(default=None),
    x_forwarded_for: str | None = Header(default=None),
) -> TokenPairResponse:
    service = AuthService(session)
    return service.refresh(request.refresh_token, user_agent=user_agent, ip_address=x_forwarded_for)


@router.post("/logout")
def logout(request: LogoutRequest, session: Session = Depends(get_session)) -> dict[str, bool]:
    service = AuthService(session)
    service.logout(request.refresh_token)
    return {"success": True}


@router.post("/password/reset")
def reset_password(
    request: PasswordResetRequest, session: Session = Depends(get_session)
) -> dict[str, bool]:
    service = AuthService(session)
    service.reset_password(request)
    return {"success": True}


@router.get("/me", response_model=UserProfileResponse)
def me(
    current_user_id: str = Depends(get_current_user_id),
    session: Session = Depends(get_session),
) -> UserProfileResponse:
    service = AuthService(session)
    user = service.repository.get_user_by_id(current_user_id)
    if user is None:
        raise NotFoundError("Current user missing")
    return UserProfileResponse(
        id=user.id,
        username=user.username,
        display_name=user.display_name,
        email=user.email,
    )
