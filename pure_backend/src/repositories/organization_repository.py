from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.identity import OrganizationMembership


class OrganizationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_user_memberships(self, user_id: str) -> list[OrganizationMembership]:
        stmt = select(OrganizationMembership).where(OrganizationMembership.user_id == user_id)
        return list(self.session.scalars(stmt))
