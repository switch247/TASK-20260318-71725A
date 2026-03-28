"""Implement organization management workflows with operation logging hooks."""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.core.errors import NotFoundError, ValidationError
from src.models.enums import MembershipStatus, RoleName
from src.models.identity import Organization, OrganizationMembership
from src.repositories.identity_repository import IdentityRepository
from src.schemas.organization import CreateOrganizationRequest, JoinOrganizationRequest
from src.services.operation_logger import OperationLogger


class OrganizationService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = IdentityRepository(session)
        self.operation_logger = OperationLogger(session)

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