from sqlalchemy.orm import Session

from src.core.errors import ForbiddenError
from src.repositories.authorization_repository import AuthorizationRepository


class AuthorizationService:
    def __init__(self, session: Session) -> None:
        self.repository = AuthorizationRepository(session)

    def enforce_membership(self, user_id: str, organization_id: str) -> str:
        membership = self.repository.find_active_membership(user_id, organization_id)
        if membership is None:
            raise ForbiddenError("User is not an active member of organization")
        return membership.role_name.value

    def enforce_permission(self, role_name: str, resource: str, action: str) -> None:
        if self.repository.has_permission(role_name, resource, action):
            return
        if self.repository.has_permission(role_name, resource, "manage"):
            return
        raise ForbiddenError(f"Missing permission: {resource}:{action}")
