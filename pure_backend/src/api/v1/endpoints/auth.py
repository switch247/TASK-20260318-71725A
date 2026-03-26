"""Expose identity APIs including recovery flow and masked profile output."""

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.orm import Session

from src.api.v1.dependencies import (
    get_current_user_id,
    get_optional_org_context,
    get_session,
)
from src.core.errors import NotFoundError
from src.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    PasswordRecoveryChallengeResponse,
    PasswordRecoveryConfirmRequest,
    PasswordRecoveryStartRequest,
    PasswordResetRequest,
    RefreshRequest,
    RegisterRequest,
    TokenPairResponse,
)
from src.schemas.user import UserProfileResponse
from src.services.auth_service import AuthService
from src.services.masking_service import mask_email

router = APIRouter(prefix="/auth")


@router.post("/register", response_model=UserProfileResponse)
def register(
    request: RegisterRequest,
    http_request: Request,
    session: Session = Depends(get_session),
) -> UserProfileResponse:
    service = AuthService(session)
    user = service.register_user(request, trace_id=http_request.headers.get("X-Trace-Id"))
    return UserProfileResponse(
        id=user.id,
        username=user.username,
        display_name=user.display_name,
        email=user.email,
    )


@router.post("/login", response_model=TokenPairResponse)
def login(
    request: LoginRequest,
    http_request: Request,
    session: Session = Depends(get_session),
    user_agent: str | None = Header(default=None),
    x_forwarded_for: str | None = Header(default=None),
) -> TokenPairResponse:
    service = AuthService(session)
    return service.login_user(
        request,
        user_agent=user_agent,
        ip_address=x_forwarded_for,
        trace_id=http_request.headers.get("X-Trace-Id"),
    )


@router.post("/refresh", response_model=TokenPairResponse)
def refresh(
    request: RefreshRequest,
    http_request: Request,
    session: Session = Depends(get_session),
    user_agent: str | None = Header(default=None),
    x_forwarded_for: str | None = Header(default=None),
) -> TokenPairResponse:
    service = AuthService(session)
    return service.refresh(
        request.refresh_token,
        user_agent=user_agent,
        ip_address=x_forwarded_for,
        trace_id=http_request.headers.get("X-Trace-Id"),
    )


@router.post("/logout")
def logout(
    request: LogoutRequest,
    http_request: Request,
    session: Session = Depends(get_session),
) -> dict[str, bool]:
    service = AuthService(session)
    service.logout(request.refresh_token, trace_id=http_request.headers.get("X-Trace-Id"))
    return {"success": True}


@router.post("/password/reset")
def reset_password(
    request: PasswordResetRequest,
    http_request: Request,
    session: Session = Depends(get_session),
) -> dict[str, bool]:
    service = AuthService(session)
    service.reset_password(request, trace_id=http_request.headers.get("X-Trace-Id"))
    return {"success": True}


@router.post("/password/recovery/start")
def start_password_recovery(
    request: PasswordRecoveryStartRequest,
    http_request: Request,
    session: Session = Depends(get_session),
 ) -> PasswordRecoveryChallengeResponse:
    service = AuthService(session)
    return service.start_password_recovery(
        request,
        trace_id=http_request.headers.get("X-Trace-Id"),
    )


@router.post("/recovery/challenge")
def recovery_challenge(
    request: PasswordRecoveryStartRequest,
    http_request: Request,
    session: Session = Depends(get_session),
) -> PasswordRecoveryChallengeResponse:
    service = AuthService(session)
    return service.start_password_recovery(
        request,
        trace_id=http_request.headers.get("X-Trace-Id"),
    )


@router.post("/password/recovery/confirm")
def confirm_password_recovery(
    request: PasswordRecoveryConfirmRequest,
    http_request: Request,
    session: Session = Depends(get_session),
) -> dict[str, bool]:
    service = AuthService(session)
    service.confirm_password_recovery(
        request,
        trace_id=http_request.headers.get("X-Trace-Id"),
    )
    return {"success": True}


@router.post("/recovery/reset")
def recovery_reset(
    request: PasswordRecoveryConfirmRequest,
    http_request: Request,
    session: Session = Depends(get_session),
) -> dict[str, bool]:
    service = AuthService(session)
    service.confirm_password_recovery(
        request,
        trace_id=http_request.headers.get("X-Trace-Id"),
    )
    return {"success": True}


@router.get("/me", response_model=UserProfileResponse)
def me(
    current_user_id: str = Depends(get_current_user_id),
    org_context: tuple[str, str] | None = Depends(get_optional_org_context),
    session: Session = Depends(get_session),
) -> UserProfileResponse:
    role_name: str | None = None
    if org_context is not None:
        _, role_name = org_context
    service = AuthService(session)
    user = service.repository.get_user_by_id(current_user_id)
    if user is None:
        raise NotFoundError("Current user missing")

    masked_email = user.email
    if masked_email is not None and role_name in {"reviewer", "general_user"}:
        masked_email = mask_email(masked_email)

    return UserProfileResponse(
        id=user.id,
        username=user.username,
        display_name=user.display_name,
        email=masked_email,
        role_name=role_name,
    )
