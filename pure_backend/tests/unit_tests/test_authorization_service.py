import pytest

from src.core.errors import ForbiddenError
from src.services.authorization_service import AuthorizationService
from src.services.demo_seed_service import seed_demo_dataset


def test_authorization_service_enforces_membership(unit_db_session) -> None:  # type: ignore[no-untyped-def]
    seeded = seed_demo_dataset(unit_db_session)
    service = AuthorizationService(unit_db_session)

    role = service.enforce_membership(
        seeded["admin_user_id"],
        seeded["organization_id"],
    )

    assert role == "administrator"


def test_authorization_service_denies_missing_permission(unit_db_session) -> None:  # type: ignore[no-untyped-def]
    service = AuthorizationService(unit_db_session)

    with pytest.raises(ForbiddenError):
        service.enforce_permission("auditor", "process", "create")
