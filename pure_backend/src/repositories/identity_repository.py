"""Provide identity-domain persistence operations for users, orgs, sessions, and recovery tokens."""

from datetime import datetime, UTC

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.identity import (
    Organization,
    OrganizationMembership,
    PasswordRecoveryToken,
    RefreshTokenSession,
    User,
)


class IdentityRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_user_by_username(self, username: str) -> User | None:
        stmt = select(User).where(User.username == username)
        return self.session.scalar(stmt)

    def get_user_by_id(self, user_id: str) -> User | None:
        stmt = select(User).where(User.id == user_id)
        return self.session.scalar(stmt)

    def create_user(self, user: User) -> User:
        self.session.add(user)
        self.session.flush()
        return user

    def create_refresh_session(self, refresh_session: RefreshTokenSession) -> RefreshTokenSession:
        self.session.add(refresh_session)
        self.session.flush()
        return refresh_session

    def find_refresh_session(self, token_hash: str) -> RefreshTokenSession | None:
        stmt = select(RefreshTokenSession).where(RefreshTokenSession.token_hash == token_hash)
        return self.session.scalar(stmt)

    def revoke_refresh_session(self, token_hash: str) -> None:
        refresh_session = self.find_refresh_session(token_hash)
        if refresh_session is not None and refresh_session.revoked_at is None:
            refresh_session.revoked_at = datetime.now(UTC)
            self.session.flush()

    def create_organization(self, organization: Organization) -> Organization:
        self.session.add(organization)
        self.session.flush()
        return organization

    def find_organization_by_code(self, code: str) -> Organization | None:
        stmt = select(Organization).where(Organization.code == code)
        return self.session.scalar(stmt)

    def create_membership(self, membership: OrganizationMembership) -> OrganizationMembership:
        self.session.add(membership)
        self.session.flush()
        return membership

    def create_password_recovery_token(
        self, recovery_token: PasswordRecoveryToken
    ) -> PasswordRecoveryToken:
        self.session.add(recovery_token)
        self.session.flush()
        return recovery_token

    def find_password_recovery_token(self, token_hash: str) -> PasswordRecoveryToken | None:
        stmt = select(PasswordRecoveryToken).where(PasswordRecoveryToken.token_hash == token_hash)
        return self.session.scalar(stmt)
