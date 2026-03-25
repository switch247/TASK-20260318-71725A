from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.enums import MembershipStatus
from src.models.identity import OrganizationMembership, RolePermission


class AuthorizationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def find_active_membership(
        self, user_id: str, organization_id: str
    ) -> OrganizationMembership | None:
        stmt = select(OrganizationMembership).where(
            OrganizationMembership.user_id == user_id,
            OrganizationMembership.organization_id == organization_id,
            OrganizationMembership.status == MembershipStatus.ACTIVE,
        )
        return self.session.scalar(stmt)

    def has_permission(self, role_name: str, resource: str, action: str) -> bool:
        stmt = select(RolePermission).where(
            RolePermission.role_name == role_name,
            RolePermission.resource == resource,
            RolePermission.action == action,
        )
        return self.session.scalar(stmt) is not None
