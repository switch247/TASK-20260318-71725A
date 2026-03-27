import os
from collections.abc import Generator
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///./test.db"
os.environ["ENFORCE_HTTPS"] = "false"

from src.api.v1.dependencies import get_current_org_context, get_current_user_id, get_session
from src.db.base import Base
from src.main import app
from src.models.enums import MembershipStatus, RoleName, WorkflowType
from src.models.identity import Organization, OrganizationMembership, User
from src.models.medical_ops import Appointment, Doctor, Expense, Patient
from src.models.operations import OperationalMetricSnapshot
from src.models.process import ProcessDefinition
from src.services.crypto_service import encrypt_sensitive, hash_password
from src.services.seed_service import seed_role_permissions

TEST_DATABASE_URL = "sqlite+pysqlite://"


@pytest.fixture
def test_session_factory() -> sessionmaker[Session]:
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


@pytest.fixture
def db_session(test_session_factory: sessionmaker[Session]) -> Generator[Session, None, None]:
    session = test_session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(
    test_session_factory: sessionmaker[Session], seeded_data: dict[str, str]
) -> Generator[TestClient, None, None]:
    def _override_get_session() -> Generator[Session, None, None]:
        session = test_session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_session] = _override_get_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def seeded_data(db_session: Session) -> dict[str, str]:
    seed_role_permissions(db_session)

    org = Organization(code="TESTORG", name="Test Org", is_active=True)
    db_session.add(org)
    db_session.flush()

    admin = User(
        username="admin_test",
        password_hash=hash_password("Admin1234"),
        display_name="Admin User",
        status="active",
    )
    db_session.add(admin)
    db_session.flush()

    db_session.add(
        OrganizationMembership(
            organization_id=org.id,
            user_id=admin.id,
            role_name=RoleName.ADMINISTRATOR,
            status=MembershipStatus.ACTIVE,
        )
    )

    reviewer = User(
        username="reviewer_test",
        password_hash=hash_password("Reviewer1234"),
        display_name="Reviewer User",
        status="active",
    )
    db_session.add(reviewer)
    db_session.flush()

    db_session.add(
        OrganizationMembership(
            organization_id=org.id,
            user_id=reviewer.id,
            role_name=RoleName.REVIEWER,
            status=MembershipStatus.ACTIVE,
        )
    )

    definition = ProcessDefinition(
        organization_id=org.id,
        name="Test Workflow",
        workflow_type=WorkflowType.CREDIT_CHANGE,
        definition_json='{"nodes":[{"key":"start"}]}',
        is_active=True,
    )
    db_session.add(definition)
    db_session.flush()

    db_session.commit()

    return {
        "organization_id": org.id,
        "admin_user_id": admin.id,
        "reviewer_user_id": reviewer.id,
        "process_definition_id": definition.id,
    }


@pytest.fixture
def role_client_factory(client: TestClient, db_session: Session):
    def _factory(user_id: str) -> TestClient:
        def _override_current_user() -> str:
            return user_id

        app.dependency_overrides[get_current_user_id] = _override_current_user
        return client

    return _factory
