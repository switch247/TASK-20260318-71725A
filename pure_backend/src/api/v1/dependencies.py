from collections.abc import Generator
from typing import Any

from fastapi import Depends, Header, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError  # type: ignore[import-untyped]
from sqlalchemy.orm import Session

from src.core.constants import ACCESS_TOKEN_TYPE
from src.core.errors import UnauthorizedError
from src.db.session import get_db_session
from src.repositories.identity_repository import IdentityRepository
from src.services.authorization_service import AuthorizationService
from src.services.crypto_service import decode_token

bearer_scheme = HTTPBearer(auto_error=False)


def get_session() -> Generator[Session, None, None]:
    yield from get_db_session()


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
    session: Session = Depends(get_session),
) -> str:
    if credentials is None:
        raise UnauthorizedError("Missing bearer token")

    token = credentials.credentials
    try:
        payload = decode_token(token)
    except JWTError as exc:
        raise UnauthorizedError("Invalid or expired token") from exc
    if payload.get("type") != ACCESS_TOKEN_TYPE:
        raise UnauthorizedError("Invalid token type")

    user_id = str(payload.get("sub"))
    repository = IdentityRepository(session)
    user = repository.get_user_by_id(user_id)
    if user is None:
        raise UnauthorizedError("User not found")
    return user_id


def get_current_org_context(
    organization_id: str = Header(default="", alias="X-Organization-Id"),
    current_user_id: str = Depends(get_current_user_id),
    session: Session = Depends(get_session),
) -> tuple[str, str]:
    if organization_id == "":
        raise UnauthorizedError("Missing X-Organization-Id header")

    authz = AuthorizationService(session)
    role_name = authz.enforce_membership(current_user_id, organization_id)
    return organization_id, role_name


def get_optional_org_context(
    organization_id: str = Header(default="", alias="X-Organization-Id"),
    current_user_id: str = Depends(get_current_user_id),
    session: Session = Depends(get_session),
) -> tuple[str, str] | None:
    if organization_id == "":
        return None

    authz = AuthorizationService(session)
    role_name = authz.enforce_membership(current_user_id, organization_id)
    return organization_id, role_name


def require_permission(resource: str, action: str) -> Any:
    def dependency(
        org_context: tuple[str, str] = Depends(get_current_org_context),
        session: Session = Depends(get_session),
    ) -> tuple[str, str]:
        organization_id, role_name = org_context
        authz = AuthorizationService(session)
        authz.enforce_permission(role_name, resource, action)
        return organization_id, role_name

    return dependency
