"""Implement identity and organization workflows with operation logging hooks."""

from datetime import datetime, timedelta, UTC
from uuid import uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.core.constants import (
    LOCKOUT_DURATION_MINUTES,
    LOCKOUT_WINDOW_MINUTES,
    MAX_LOGIN_ATTEMPTS,
    REFRESH_TOKEN_TYPE,
)
from src.core.errors import NotFoundError, UnauthorizedError, ValidationError
from src.core.security import validate_password_policy
from src.models.enums import MembershipStatus, RoleName, UserStatus
from src.models.identity import (
    Organization,
    OrganizationMembership,
    PasswordRecoveryToken,
    RefreshTokenSession,
    User,
)
from src.repositories.identity_repository import IdentityRepository
from src.schemas.auth import (
    LoginRequest,
    PasswordRecoveryConfirmRequest,
    PasswordRecoveryStartRequest,
    PasswordResetRequest,
    RegisterRequest,
    TokenPairResponse,
)
from src.schemas.organization import CreateOrganizationRequest, JoinOrganizationRequest
from src.services.crypto_service import (
    build_access_token,
    build_refresh_token,
    decode_token,
    decrypt_sensitive,
    encrypt_sensitive,
    hash_password,
    sha256_text,
    verify_password,
)
from src.services.operation_logger import OperationLogger


class AuthService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = IdentityRepository(session)
        self.operation_logger = OperationLogger(session)

    def register_user(self, request: RegisterRequest, trace_id: str | None = None) -> User:
        if not validate_password_policy(request.password):
            raise ValidationError(
                "Password must be at least 8 characters and contain letters and numbers",
            )

        existing_user = self.repository.get_user_by_username(request.username)
        if existing_user is not None:
            raise ValidationError("Username already exists")

        encrypted_email = None
        if request.email is not None and request.email != "":
            encrypted_email = encrypt_sensitive(request.email)

        user = User(
            username=request.username,
            password_hash=hash_password(request.password),
            display_name=request.display_name,
            email_encrypted=encrypted_email,
            status=UserStatus.ACTIVE,
        )
        self.repository.create_user(user)
        self.operation_logger.log(
            actor_id=user.id,
            organization_id=None,
            resource_type="user",
            resource_id=user.id,
            operation="create",
            trace_id=trace_id,
            before=None,
            after={"username": user.username, "display_name": user.display_name},
        )
        self.session.commit()
        self.session.refresh(user)
        return user

    def login_user(
        self,
        request: LoginRequest,
        user_agent: str | None,
        ip_address: str | None,
        trace_id: str | None = None,
    ) -> TokenPairResponse:
        user = self.repository.get_user_by_username(request.username)
        if user is None:
            raise UnauthorizedError("Invalid username or password")

        self._validate_lockout(user)
        self._validate_user_status(user)

        if not verify_password(request.password, user.password_hash):
            self._record_login_failure(user)
            self.session.commit()
            raise UnauthorizedError("Invalid username or password")

        self._clear_login_failures(user)

        access_token, expires_in = build_access_token(user.id)
        refresh_token = build_refresh_token(user.id)
        token_hash = sha256_text(refresh_token)
        expires_at = datetime.now(UTC) + timedelta(days=7)

        self.repository.create_refresh_session(
            RefreshTokenSession(
                user_id=user.id,
                token_hash=token_hash,
                expires_at=expires_at,
                user_agent=user_agent,
                ip_address=ip_address,
            )
        )
        self.operation_logger.log(
            actor_id=user.id,
            organization_id=None,
            resource_type="auth",
            resource_id=user.id,
            operation="login",
            trace_id=trace_id,
            after={"username": user.username},
        )
        self.session.commit()
        return TokenPairResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
        )

    def refresh(
        self,
        refresh_token: str,
        user_agent: str | None,
        ip_address: str | None,
        trace_id: str | None = None,
    ) -> TokenPairResponse:
        payload = decode_token(refresh_token)
        if payload.get("type") != REFRESH_TOKEN_TYPE:
            raise UnauthorizedError("Invalid token type")

        user_id = str(payload.get("sub"))
        token_hash = sha256_text(refresh_token)
        refresh_session = self.repository.find_refresh_session(token_hash)

        if refresh_session is None or refresh_session.revoked_at is not None:
            raise UnauthorizedError("Refresh token revoked")
        if refresh_session.expires_at < datetime.now(UTC):
            raise UnauthorizedError("Refresh token expired")

        self.repository.revoke_refresh_session(token_hash)

        access_token, expires_in = build_access_token(user_id)
        new_refresh_token = build_refresh_token(user_id)
        new_hash = sha256_text(new_refresh_token)

        self.repository.create_refresh_session(
            RefreshTokenSession(
                user_id=user_id,
                token_hash=new_hash,
                expires_at=datetime.now(UTC) + timedelta(days=7),
                user_agent=user_agent,
                ip_address=ip_address,
            )
        )
        self.operation_logger.log(
            actor_id=user_id,
            organization_id=None,
            resource_type="auth",
            resource_id=user_id,
            operation="refresh",
            trace_id=trace_id,
            after={"token_rotated": True},
        )
        self.session.commit()

        return TokenPairResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=expires_in,
        )

    def logout(self, refresh_token: str, trace_id: str | None = None) -> None:
        token_hash = sha256_text(refresh_token)
        self.repository.revoke_refresh_session(token_hash)
        self.operation_logger.log(
            actor_id=None,
            organization_id=None,
            resource_type="auth",
            resource_id=None,
            operation="logout",
            trace_id=trace_id,
            after={"token_revoked": True},
        )
        self.session.commit()

    def reset_password(self, request: PasswordResetRequest, trace_id: str | None = None) -> None:
        if not validate_password_policy(request.new_password):
            raise ValidationError(
                "Password must be at least 8 characters and contain letters and numbers",
            )

        user = self.repository.get_user_by_username(request.username)
        if user is None:
            raise NotFoundError("User not found")

        token_hash = sha256_text(request.recovery_token)
        recovery = self.repository.find_password_recovery_token(token_hash)
        if recovery is None or recovery.user_id != user.id:
            raise UnauthorizedError("Invalid recovery token")
        if recovery.used_at is not None:
            raise UnauthorizedError("Recovery token already used")
        if recovery.expires_at < datetime.now(UTC):
            raise UnauthorizedError("Recovery token expired")

        user.password_hash = hash_password(request.new_password)
        user.failed_login_count = 0
        user.failed_login_window_start = None
        user.locked_until = None
        user.status = UserStatus.ACTIVE
        recovery.used_at = datetime.now(UTC)
        self.operation_logger.log(
            actor_id=user.id,
            organization_id=None,
            resource_type="user",
            resource_id=user.id,
            operation="password_reset",
            trace_id=trace_id,
            after={"username": user.username},
        )
        self.session.commit()

    def start_password_recovery(
        self, request: PasswordRecoveryStartRequest, trace_id: str | None = None
    ) -> dict[str, str]:
        user = self.repository.get_user_by_username(request.username)
        if user is None:
            raise NotFoundError("User not found")

        raw_token = f"recovery-{uuid4().hex}-{uuid4().hex}"
        token_hash = sha256_text(raw_token)
        expires_at = datetime.now(UTC) + timedelta(minutes=15)
        recovery = PasswordRecoveryToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
            used_at=None,
        )
        self.repository.create_password_recovery_token(recovery)
        self.operation_logger.log(
            actor_id=user.id,
            organization_id=None,
            resource_type="password_recovery",
            resource_id=recovery.id,
            operation="create",
            trace_id=trace_id,
            after={"username": user.username, "expires_at": expires_at.isoformat()},
        )
        self.session.commit()
        return {"recovery_token": raw_token, "challenge_type": "signed_token"}

    def confirm_password_recovery(
        self, request: PasswordRecoveryConfirmRequest, trace_id: str | None = None
    ) -> None:
        if not validate_password_policy(request.new_password):
            raise ValidationError(
                "Password must be at least 8 characters and contain letters and numbers",
            )

        user = self.repository.get_user_by_username(request.username)
        if user is None:
            raise NotFoundError("User not found")

        token_hash = sha256_text(request.recovery_token)
        recovery = self.repository.find_password_recovery_token(token_hash)
        if recovery is None or recovery.user_id != user.id:
            raise UnauthorizedError("Invalid recovery token")
        if recovery.used_at is not None:
            raise UnauthorizedError("Recovery token already used")
        if recovery.expires_at < datetime.now(UTC):
            raise UnauthorizedError("Recovery token expired")

        user.password_hash = hash_password(request.new_password)
        user.failed_login_count = 0
        user.failed_login_window_start = None
        user.locked_until = None
        user.status = UserStatus.ACTIVE
        recovery.used_at = datetime.now(UTC)

        self.operation_logger.log(
            actor_id=user.id,
            organization_id=None,
            resource_type="password_recovery",
            resource_id=recovery.id,
            operation="confirm",
            trace_id=trace_id,
            after={"username": user.username, "used": True},
        )
        self.session.commit()

    def create_organization(
        self, request: CreateOrganizationRequest, user_id: str, trace_id: str | None = None
    ) -> Organization:
        organization = Organization(code=request.code, name=request.name, is_active=True)

        try:
            self.repository.create_organization(organization)
            self.repository.create_membership(
                OrganizationMembership(
                    organization_id=organization.id,
                    user_id=user_id,
                    role_name=RoleName.ADMINISTRATOR,
                    status=MembershipStatus.ACTIVE,
                )
            )
            self.operation_logger.log(
                actor_id=user_id,
                organization_id=organization.id,
                resource_type="organization",
                resource_id=organization.id,
                operation="create",
                trace_id=trace_id,
                after={"code": organization.code, "name": organization.name},
            )
            self.session.commit()
            self.session.refresh(organization)
            return organization
        except IntegrityError as exc:
            self.session.rollback()
            raise ValidationError("Organization code already exists") from exc

    def join_organization(
        self,
        request: JoinOrganizationRequest,
        user_id: str,
        trace_id: str | None = None,
    ) -> OrganizationMembership:
        organization = self.repository.find_organization_by_code(request.organization_code)
        if organization is None:
            raise NotFoundError("Organization not found")

        membership = OrganizationMembership(
            organization_id=organization.id,
            user_id=user_id,
            role_name=RoleName.GENERAL_USER,
            status=MembershipStatus.ACTIVE,
        )
        try:
            self.repository.create_membership(membership)
            self.operation_logger.log(
                actor_id=user_id,
                organization_id=organization.id,
                resource_type="organization_membership",
                resource_id=membership.id,
                operation="create",
                trace_id=trace_id,
                after={"organization_id": organization.id, "role_name": membership.role_name.value},
            )
            self.session.commit()
            self.session.refresh(membership)
            return membership
        except IntegrityError as exc:
            self.session.rollback()
            raise ValidationError("User already joined organization") from exc

    def decrypt_email(self, user: User) -> str | None:
        if user.email_encrypted is None:
            return None
        return decrypt_sensitive(user.email_encrypted)

    def _validate_lockout(self, user: User) -> None:
        now = datetime.now(UTC)
        if user.locked_until is not None and user.locked_until > now:
            raise UnauthorizedError("Account locked due to repeated login failures")

        if user.status == UserStatus.LOCKED and (
            user.locked_until is None or user.locked_until <= now
        ):
            user.status = UserStatus.ACTIVE
            user.locked_until = None
            user.failed_login_count = 0
            user.failed_login_window_start = None

    def _validate_user_status(self, user: User) -> None:
        if user.status == UserStatus.DISABLED:
            raise UnauthorizedError("Account is disabled")
        if user.status == UserStatus.LOCKED:
            raise UnauthorizedError("Account locked due to repeated login failures")

    def _record_login_failure(self, user: User) -> None:
        now = datetime.now(UTC)

        if user.failed_login_window_start is None:
            user.failed_login_window_start = now
            user.failed_login_count = 1
            return

        window_delta = now - user.failed_login_window_start
        if window_delta > timedelta(minutes=LOCKOUT_WINDOW_MINUTES):
            user.failed_login_window_start = now
            user.failed_login_count = 1
            return

        user.failed_login_count += 1
        if user.failed_login_count >= MAX_LOGIN_ATTEMPTS:
            user.status = UserStatus.LOCKED
            user.locked_until = now + timedelta(minutes=LOCKOUT_DURATION_MINUTES)

    def _clear_login_failures(self, user: User) -> None:
        user.failed_login_count = 0
        user.failed_login_window_start = None
        user.locked_until = None
        user.status = UserStatus.ACTIVE
