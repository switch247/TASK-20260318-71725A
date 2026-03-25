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
from src.services.crypto_service import hash_password
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
def seeded_data(db_session: Session) -> dict[str, str]:
    seed_role_permissions(db_session)

    organization = Organization(code="ORG-001", name="Test Org", is_active=True)
    organization_two = Organization(code="ORG-002", name="Other Org", is_active=True)
    db_session.add_all([organization, organization_two])
    db_session.flush()

    admin_user = User(
        username="admin_test",
        password_hash=hash_password("Admin1234"),
        display_name="Admin Tester",
        email="admin@test.local",
    )
    reviewer_user = User(
        username="reviewer_test",
        password_hash=hash_password("Review1234"),
        display_name="Reviewer Tester",
        email="reviewer@test.local",
    )
    general_user = User(
        username="general_test",
        password_hash=hash_password("General1234"),
        display_name="General Tester",
        email="general@test.local",
    )
    auditor_user = User(
        username="auditor_test",
        password_hash=hash_password("Auditor1234"),
        display_name="Auditor Tester",
        email="auditor@test.local",
    )
    outsider_user = User(
        username="outsider_test",
        password_hash=hash_password("Outsider1234"),
        display_name="Outsider Tester",
        email="outsider@test.local",
    )
    db_session.add_all([admin_user, reviewer_user, general_user, auditor_user, outsider_user])
    db_session.flush()

    db_session.add_all(
        [
            OrganizationMembership(
                organization_id=organization.id,
                user_id=admin_user.id,
                role_name=RoleName.ADMINISTRATOR,
                status=MembershipStatus.ACTIVE,
            ),
            OrganizationMembership(
                organization_id=organization.id,
                user_id=reviewer_user.id,
                role_name=RoleName.REVIEWER,
                status=MembershipStatus.ACTIVE,
            ),
            OrganizationMembership(
                organization_id=organization.id,
                user_id=general_user.id,
                role_name=RoleName.GENERAL_USER,
                status=MembershipStatus.ACTIVE,
            ),
            OrganizationMembership(
                organization_id=organization_two.id,
                user_id=outsider_user.id,
                role_name=RoleName.GENERAL_USER,
                status=MembershipStatus.ACTIVE,
            ),
            OrganizationMembership(
                organization_id=organization.id,
                user_id=auditor_user.id,
                role_name=RoleName.AUDITOR,
                status=MembershipStatus.ACTIVE,
            ),
        ]
    )

    process_definition = ProcessDefinition(
        organization_id=organization.id,
        name="Test Process",
        workflow_type=WorkflowType.RESOURCE_APPLICATION,
        version=1,
        is_active=True,
        definition_json='{"nodes":[{"key":"review-node-1","type":"approval"}]}',
    )
    db_session.add(process_definition)

    patient = Patient(
        organization_id=organization.id,
        patient_number="P-001",
        name="Patient One",
        contact_encrypted="encrypted-contact",
    )
    doctor = Doctor(
        organization_id=organization.id,
        doctor_number="D-001",
        name="Doctor One",
        department="Cardiology",
    )
    db_session.add_all([patient, doctor])
    db_session.flush()

    db_session.add_all(
        [
            Appointment(
                organization_id=organization.id,
                patient_id=patient.id,
                doctor_id=doctor.id,
                scheduled_at=datetime.now(UTC) + timedelta(hours=6),
                status="scheduled",
                anomaly_flag=None,
            ),
            Expense(
                organization_id=organization.id,
                patient_id=patient.id,
                doctor_id=doctor.id,
                expense_type="consultation",
                amount=200.0,
            ),
            OperationalMetricSnapshot(
                organization_id=organization.id,
                metric_code="activity",
                snapshot_at=datetime.now(UTC) - timedelta(minutes=15),
                metric_value=75.0,
                dimensions_json='{"department":"Cardiology"}',
            ),
            OperationalMetricSnapshot(
                organization_id=organization.id,
                metric_code="message_reach",
                snapshot_at=datetime.now(UTC) - timedelta(minutes=20),
                metric_value=61.0,
                dimensions_json='{"channel":"sms"}',
            ),
            OperationalMetricSnapshot(
                organization_id=organization.id,
                metric_code="attendance_anomaly",
                snapshot_at=datetime.now(UTC) - timedelta(minutes=30),
                metric_value=2.0,
                dimensions_json='{"severity":"low"}',
            ),
            OperationalMetricSnapshot(
                organization_id=organization.id,
                metric_code="work_order_sla",
                snapshot_at=datetime.now(UTC) - timedelta(minutes=40),
                metric_value=96.5,
                dimensions_json='{"window":"24h"}',
            ),
        ]
    )

    db_session.commit()

    return {
        "organization_id": organization.id,
        "organization_two_id": organization_two.id,
        "admin_user_id": admin_user.id,
        "reviewer_user_id": reviewer_user.id,
        "general_user_id": general_user.id,
        "auditor_user_id": auditor_user.id,
        "outsider_user_id": outsider_user.id,
        "process_definition_id": process_definition.id,
    }


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

    def _override_get_current_user_id() -> str:
        return seeded_data["admin_user_id"]

    def _override_get_current_org_context() -> tuple[str, str]:
        return seeded_data["organization_id"], RoleName.ADMINISTRATOR.value

    app.dependency_overrides[get_session] = _override_get_session
    app.dependency_overrides[get_current_user_id] = _override_get_current_user_id
    app.dependency_overrides[get_current_org_context] = _override_get_current_org_context

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def role_client_factory(
    test_session_factory: sessionmaker[Session], seeded_data: dict[str, str]
) -> Generator:
    def _make_client(user_id: str) -> TestClient:
        def _override_get_session() -> Generator[Session, None, None]:
            session = test_session_factory()
            try:
                yield session
            finally:
                session.close()

        def _override_get_current_user_id() -> str:
            return user_id

        app.dependency_overrides[get_session] = _override_get_session
        app.dependency_overrides[get_current_user_id] = _override_get_current_user_id
        return TestClient(app)

    yield _make_client
    app.dependency_overrides.clear()
