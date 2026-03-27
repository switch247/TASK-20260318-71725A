# import os
# from collections.abc import Generator
# from datetime import UTC, datetime, timedelta

# import pytest
# from fastapi.testclient import TestClient
# from sqlalchemy import create_engine
# from sqlalchemy.orm import Session, sessionmaker
# from sqlalchemy.pool import StaticPool

# os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///./test.db")
# os.environ.setdefault("ENFORCE_HTTPS", "false")

# # Determine test DB URL and ensure the application uses it when modules import
# TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL", "sqlite+pysqlite://")
# os.environ["DATABASE_URL"] = TEST_DATABASE_URL

# from fastapi import Depends, Header, Security
# from fastapi.security import HTTPAuthorizationCredentials
# from src.api.v1.dependencies import (
#     get_current_org_context,
#     get_current_user_id,
#     get_session,
#     bearer_scheme,
# )
# from src.db.base import Base
# import src.models  # register all models
# from src.models.enums import MembershipStatus, RoleName, WorkflowType
# from src.models.identity import Organization, OrganizationMembership, User
# from src.models.medical_ops import Appointment, Doctor, Expense, Patient
# from src.models.operations import OperationalMetricSnapshot
# from src.models.process import ProcessDefinition
# from src.services.crypto_service import encrypt_sensitive, hash_password
# from src.services.seed_service import seed_role_permissions



# # Ensure application uses the test DB URL during tests so app-level SessionLocal
# # is created against the same database as test engines
# os.environ["DATABASE_URL"] = TEST_DATABASE_URL


# @pytest.fixture
# def test_session_factory() -> sessionmaker[Session]:
#     connect_args = {"check_same_thread": False} if "sqlite" in TEST_DATABASE_URL else {}
#     poolclass = StaticPool if "sqlite" in TEST_DATABASE_URL else None
    
#     engine_kwargs = {}
#     if connect_args:
#         engine_kwargs["connect_args"] = connect_args
#     if poolclass:
#         engine_kwargs["poolclass"] = poolclass

#     engine = create_engine(TEST_DATABASE_URL, **engine_kwargs)

#     # Create a session factory for tests and bind the application to use it
#     test_session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)

#     # Bind the application's session to the same test engine so SessionLocal()
#     # used by application code points to the same database as the test fixtures.
#     import src.db.session as app_db_session

#     app_db_session.engine = engine
#     app_db_session.SessionLocal = test_session_factory

#     # Ensure a clean schema for each test run to avoid unique constraint conflicts
#     Base.metadata.drop_all(bind=engine)
#     Base.metadata.create_all(bind=engine)
#     return test_session_factory


# @pytest.fixture
# def db_session(test_session_factory: sessionmaker[Session]) -> Generator[Session, None, None]:
#     session = test_session_factory()
#     try:
#         yield session
#     finally:
#         session.close()


# @pytest.fixture
# def client(
#     test_session_factory: sessionmaker[Session], seeded_data: dict[str, str]
# ) -> Generator[TestClient, None, None]:
#     def _override_get_session() -> Generator[Session, None, None]:
#         session = test_session_factory()
#         try:
#             yield session
#         finally:
#             session.close()

#     # Import the FastAPI `app` after the test DB and SessionLocal are configured
#     # so the application's startup code (lifespan) uses the test database.
#     from src.main import app

#     # Default session override so application uses the test session factory
#     app.dependency_overrides[get_session] = _override_get_session

#     # Provide identity overrides that defer to real token validation when a
#     # bearer token is provided, otherwise fall back to the seeded admin user/org.
#     def _override_current_user_default(
#         credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
#         session: Session = Depends(get_session),
#     ) -> str:
#         if credentials is not None:
#             return get_current_user_id(credentials=credentials, session=session)
#         return seeded_data["admin_user_id"]

#     def _override_org_context_default(
#         organization_id: str = Header(default="", alias="X-Organization-Id"),
#         credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
#         session: Session = Depends(get_session),
#     ) -> tuple[str, str]:
#         if credentials is not None:
#             # will raise if header missing or membership invalid
#             user_id = get_current_user_id(credentials=credentials, session=session)
#             return get_current_org_context(organization_id=organization_id, current_user_id=user_id, session=session)
#         return (seeded_data["organization_id"], RoleName.ADMINISTRATOR)

#     app.dependency_overrides[get_current_user_id] = _override_current_user_default
#     app.dependency_overrides[get_current_org_context] = _override_org_context_default
#     with TestClient(app) as test_client:
#         yield test_client
#     app.dependency_overrides.clear()


# @pytest.fixture
# def seeded_data(db_session: Session) -> dict[str, str]:
#     seed_role_permissions(db_session)

#     org = Organization(code="TESTORG", name="Test Org", is_active=True)
#     db_session.add(org)
#     db_session.flush()

#     admin = User(
#         username="admin_test",
#         password_hash=hash_password("Admin1234"),
#         display_name="Admin User",
#         status="active",
#         email_encrypted=encrypt_sensitive("admin_test@example.com"),
#     )
#     db_session.add(admin)
#     db_session.flush()
#     # Create reviewer, general user and auditor as well
#     reviewer = User(
#         username="reviewer_test",
#         password_hash=hash_password("Reviewer1234"),
#         display_name="Reviewer User",
#         status="active",
#         email_encrypted=encrypt_sensitive("reviewer_test@example.com"),
#     )
#     general_user = User(
#         username="user_test",
#         password_hash=hash_password("User12345"),
#         display_name="General User",
#         status="active",
#         email_encrypted=encrypt_sensitive("user_test@example.com"),
#     )
#     auditor = User(
#         username="auditor_test",
#         password_hash=hash_password("Audit12345"),
#         display_name="Auditor User",
#         status="active",
#         email_encrypted=encrypt_sensitive("auditor_test@example.com"),
#     )
#     db_session.add_all([reviewer, general_user, auditor])
#     db_session.flush()

#     db_session.add_all(
#         [
#             OrganizationMembership(
#                 organization_id=org.id,
#                 user_id=admin.id,
#                 role_name=RoleName.ADMINISTRATOR,
#                 status=MembershipStatus.ACTIVE,
#             ),
#             OrganizationMembership(
#                 organization_id=org.id,
#                 user_id=reviewer.id,
#                 role_name=RoleName.REVIEWER,
#                 status=MembershipStatus.ACTIVE,
#             ),
#             OrganizationMembership(
#                 organization_id=org.id,
#                 user_id=general_user.id,
#                 role_name=RoleName.GENERAL_USER,
#                 status=MembershipStatus.ACTIVE,
#             ),
#             OrganizationMembership(
#                 organization_id=org.id,
#                 user_id=auditor.id,
#                 role_name=RoleName.AUDITOR,
#                 status=MembershipStatus.ACTIVE,
#             ),
#         ]
#     )

#     definition = ProcessDefinition(
#         organization_id=org.id,
#         name="Test Workflow",
#         workflow_type=WorkflowType.CREDIT_CHANGE,
#         definition_json='{"nodes":[{"key":"start"}]}',
#         is_active=True,
#     )
#     db_session.add(definition)
#     db_session.flush()

#     # Add some operational metrics so analytics endpoints return data
#     metric_1 = OperationalMetricSnapshot(
#         organization_id=org.id,
#         metric_code="activity",
#         snapshot_at=datetime.now(UTC) - timedelta(hours=1),
#         metric_value=42.0,
#         dimensions_json='{"department":"Cardiology"}',
#     )
#     metric_2 = OperationalMetricSnapshot(
#         organization_id=org.id,
#         metric_code="message_reach",
#         snapshot_at=datetime.now(UTC) - timedelta(hours=2),
#         metric_value=10.0,
#         dimensions_json='{"channel":"sms"}',
#     )
#     db_session.add_all([metric_1, metric_2])

#     # Create a patient and doctor then add appointment and expense
#     patient = Patient(
#         organization_id=org.id,
#         patient_number="P-TEST-1",
#         name="Alice",
#         contact_encrypted=encrypt_sensitive("13800002222"),
#     )
#     doctor = Doctor(
#         organization_id=org.id,
#         doctor_number="D-TEST-1",
#         name="Doctor Bob",
#         department="Cardiology",
#     )
#     db_session.add_all([patient, doctor])
#     db_session.flush()

#     appointment = Appointment(
#         organization_id=org.id,
#         patient_id=patient.id,
#         doctor_id=doctor.id,
#         scheduled_at=datetime.now(UTC) + timedelta(days=1),
#         status="scheduled",
#         anomaly_flag=None,
#     )
#     expense = Expense(
#         organization_id=org.id,
#         patient_id=patient.id,
#         doctor_id=doctor.id,
#         expense_type="consultation",
#         amount=50.0,
#     )
#     db_session.add_all([appointment, expense])


#     # Add remaining operational metrics
#     metric_3 = OperationalMetricSnapshot(
#         organization_id=org.id,
#         metric_code="attendance_anomaly",
#         snapshot_at=datetime.now(UTC) - timedelta(hours=3),
#         metric_value=3.0,
#         dimensions_json='{"severity":"medium"}',
#     )
#     metric_4 = OperationalMetricSnapshot(
#         organization_id=org.id,
#         metric_code="work_order_sla",
#         snapshot_at=datetime.now(UTC) - timedelta(hours=4),
#         metric_value=97.0,
#         dimensions_json='{"window":"24h"}',
#     )
#     db_session.add_all([metric_3, metric_4])

#     db_session.commit()

#     # Create an outsider organization and user (for RBAC/security tests)
#     outsider_org = Organization(code="OUTSIDE", name="Outside Org", is_active=True)
#     db_session.add(outsider_org)
#     db_session.flush()

#     outsider_user = User(
#         username="outsider_test",
#         password_hash=hash_password("Outside123"),
#         display_name="Outsider User",
#         status="active",
#         email_encrypted=encrypt_sensitive("outsider_test@example.com"),
#     )
#     db_session.add(outsider_user)
#     db_session.flush()

#     db_session.add(
#         OrganizationMembership(
#             organization_id=outsider_org.id,
#             user_id=outsider_user.id,
#             role_name=RoleName.GENERAL_USER,
#             status=MembershipStatus.ACTIVE,
#         )
#     )

#     db_session.commit()

#     return {
#         "organization_id": org.id,
#         "admin_user_id": admin.id,
#         "reviewer_user_id": reviewer.id,
#         "general_user_id": general_user.id,
#         "auditor_user_id": auditor.id,
#         "outsider_user_id": outsider_user.id,
#         "process_definition_id": definition.id,
#     }


# @pytest.fixture
# def role_client_factory(client: TestClient, db_session: Session):
#     def _factory(user_id: str) -> TestClient:
#         def _override_current_user() -> str:
#             return user_id

#         # Import app here (delayed) so it exists in this scope and is configured
#         from src.main import app
#         # Also override org context to return the membership role for this user
#         def _override_org_context_for_user() -> tuple[str, str]:
#             membership = (
#                 db_session.query(OrganizationMembership)
#                 .filter(
#                     OrganizationMembership.user_id == user_id,
#                     OrganizationMembership.status == MembershipStatus.ACTIVE,
#                 )
#                 .first()
#             )
#             if membership is None:
#                 raise RuntimeError("User has no active membership for any organization")
#             return (membership.organization_id, membership.role_name.value)

#         app.dependency_overrides[get_current_user_id] = _override_current_user
#         app.dependency_overrides[get_current_org_context] = _override_org_context_for_user
#         return client

#     return _factory



import os
from collections.abc import Generator
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///./test.db")
os.environ.setdefault("ENFORCE_HTTPS", "false")
# Allow governance service to write stub backups in test environments
os.environ.setdefault("ALLOW_GOVERNANCE_BACKUP_STUB", "true")

# Determine test DB URL and ensure the application uses it when modules import
# Default to a file-backed SQLite DB to avoid race conditions with in-memory DBs
TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL", "sqlite+pysqlite:///./test.db")
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

from fastapi import Depends, Header, Security
from fastapi.security import HTTPAuthorizationCredentials
from src.api.v1.dependencies import get_current_org_context, get_current_user_id, get_session, bearer_scheme
from src.db.base import Base
import src.models  # register all models
from src.models.enums import MembershipStatus, RoleName, WorkflowType
from src.models.identity import Organization, OrganizationMembership, User
from src.core.errors import ForbiddenError
from src.models.medical_ops import Appointment, Doctor, Expense, Patient
from src.models.operations import OperationalMetricSnapshot
from src.models.process import ProcessDefinition
from src.services.crypto_service import encrypt_sensitive, hash_password
from src.services.seed_service import seed_role_permissions


# Ensure application uses the test DB URL during tests so app-level SessionLocal
# is created against the same database as test engines
os.environ["DATABASE_URL"] = TEST_DATABASE_URL


@pytest.fixture
def test_session_factory() -> sessionmaker[Session]:
    connect_args = {"check_same_thread": False} if "sqlite" in TEST_DATABASE_URL else {}
    poolclass = StaticPool if "sqlite" in TEST_DATABASE_URL else None
    
    engine_kwargs = {}
    if connect_args:
        engine_kwargs["connect_args"] = connect_args
    if poolclass:
        engine_kwargs["poolclass"] = poolclass

    engine = create_engine(TEST_DATABASE_URL, **engine_kwargs)

    # Create a session factory for tests and bind the application to use it
    test_session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    # Bind the application's session to the same test engine so SessionLocal()
    # used by application code points to the same database as the test fixtures.
    import src.db.session as app_db_session

    app_db_session.engine = engine
    app_db_session.SessionLocal = test_session_factory

    # Ensure a clean schema for each test run to avoid unique constraint conflicts
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    return test_session_factory


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

    # Import the FastAPI `app` after the test DB and SessionLocal are configured
    # so the application's startup code (lifespan) uses the test database.
    from src.main import app

    # Default session override so application uses the test session factory
    # Provide identity overrides that respect a real Authorization header when present
    def _override_current_user_default(
        credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
        session: Session = Depends(get_session),
    ) -> str:
        if credentials is not None:
            return get_current_user_id(credentials=credentials, session=session)
        return seeded_data["admin_user_id"]

    def _override_org_context_default(
        organization_id: str = Header(default="", alias="X-Organization-Id"),
        credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
        session: Session = Depends(get_session),
    ) -> tuple[str, str]:
        if credentials is not None:
            user_id = get_current_user_id(credentials=credentials, session=session)
            return get_current_org_context(organization_id=organization_id, current_user_id=user_id, session=session)
        return (seeded_data["organization_id"], RoleName.ADMINISTRATOR)

    app.dependency_overrides[get_current_user_id] = _override_current_user_default
    app.dependency_overrides[get_current_org_context] = _override_org_context_default
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
        email_encrypted=encrypt_sensitive("admin_test@example.com"),
    )
    db_session.add(admin)
    db_session.flush()
    # Create reviewer, general user and auditor as well
    reviewer = User(
        username="reviewer_test",
        password_hash=hash_password("Review1234"),
        display_name="Reviewer User",
        status="active",
        email_encrypted=encrypt_sensitive("reviewer_test@example.com"),
    )
    general_user = User(
        username="user_test",
        password_hash=hash_password("User12345"),
        display_name="General User",
        status="active",
        email_encrypted=encrypt_sensitive("user_test@example.com"),
    )
    auditor = User(
        username="auditor_test",
        password_hash=hash_password("Audit12345"),
        display_name="Auditor User",
        status="active",
        email_encrypted=encrypt_sensitive("auditor_test@example.com"),
    )
    db_session.add_all([reviewer, general_user, auditor])
    db_session.flush()

    db_session.add_all(
        [
            OrganizationMembership(
                organization_id=org.id,
                user_id=admin.id,
                role_name=RoleName.ADMINISTRATOR,
                status=MembershipStatus.ACTIVE,
            ),
            OrganizationMembership(
                organization_id=org.id,
                user_id=reviewer.id,
                role_name=RoleName.REVIEWER,
                status=MembershipStatus.ACTIVE,
            ),
            OrganizationMembership(
                organization_id=org.id,
                user_id=general_user.id,
                role_name=RoleName.GENERAL_USER,
                status=MembershipStatus.ACTIVE,
            ),
            OrganizationMembership(
                organization_id=org.id,
                user_id=auditor.id,
                role_name=RoleName.AUDITOR,
                status=MembershipStatus.ACTIVE,
            ),
        ]
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

    # Add some operational metrics so analytics endpoints return data
    metric_1 = OperationalMetricSnapshot(
        organization_id=org.id,
        metric_code="activity",
        snapshot_at=datetime.now(UTC) - timedelta(hours=1),
        metric_value=42.0,
        dimensions_json='{"department":"Cardiology"}',
    )
    metric_2 = OperationalMetricSnapshot(
        organization_id=org.id,
        metric_code="message_reach",
        snapshot_at=datetime.now(UTC) - timedelta(hours=2),
        metric_value=10.0,
        dimensions_json='{"channel":"sms"}',
    )
    db_session.add_all([metric_1, metric_2])

    # Create a patient and doctor then add appointment and expense
    patient = Patient(
        organization_id=org.id,
        patient_number="P-TEST-1",
        name="Alice",
        contact_encrypted=encrypt_sensitive("13800002222"),
    )
    doctor = Doctor(
        organization_id=org.id,
        doctor_number="D-TEST-1",
        name="Doctor Bob",
        department="Cardiology",
    )
    db_session.add_all([patient, doctor])
    db_session.flush()

    appointment = Appointment(
        organization_id=org.id,
        patient_id=patient.id,
        doctor_id=doctor.id,
        scheduled_at=datetime.now(UTC) + timedelta(days=1),
        status="scheduled",
        anomaly_flag=None,
    )
    expense = Expense(
        organization_id=org.id,
        patient_id=patient.id,
        doctor_id=doctor.id,
        expense_type="consultation",
        amount=50.0,
    )
    db_session.add_all([appointment, expense])


    # Add remaining operational metrics
    metric_3 = OperationalMetricSnapshot(
        organization_id=org.id,
        metric_code="attendance_anomaly",
        snapshot_at=datetime.now(UTC) - timedelta(hours=3),
        metric_value=3.0,
        dimensions_json='{"severity":"medium"}',
    )
    metric_4 = OperationalMetricSnapshot(
        organization_id=org.id,
        metric_code="work_order_sla",
        snapshot_at=datetime.now(UTC) - timedelta(hours=4),
        metric_value=97.0,
        dimensions_json='{"window":"24h"}',
    )
    db_session.add_all([metric_3, metric_4])

    db_session.commit()

    # Create an outsider organization and user (for RBAC/security tests)
    outsider_org = Organization(code="OUTSIDE", name="Outside Org", is_active=True)
    db_session.add(outsider_org)
    db_session.flush()

    # Also create a second organization to exercise cross-organization scenarios
    organization_two = Organization(code="OUTSIDE2", name="Outside Org 2", is_active=True)
    db_session.add(organization_two)
    db_session.flush()

    outsider_user = User(
        username="outsider_test",
        password_hash=hash_password("Outside123"),
        display_name="Outsider User",
        status="active",
        email_encrypted=encrypt_sensitive("outsider_test@example.com"),
    )
    db_session.add(outsider_user)
    db_session.flush()

    db_session.add(
        OrganizationMembership(
            organization_id=outsider_org.id,
            user_id=outsider_user.id,
            role_name=RoleName.GENERAL_USER,
            status=MembershipStatus.ACTIVE,
        )
    )

    # Also add membership for the outsider in the second organization so tests
    # that post as the outsider to `organization_two` are valid.
    db_session.add(
        OrganizationMembership(
            organization_id=organization_two.id,
            user_id=outsider_user.id,
            role_name=RoleName.GENERAL_USER,
            status=MembershipStatus.ACTIVE,
        )
    )

    db_session.commit()

    return {
        "organization_id": org.id,
        "organization_two_id": organization_two.id,
        "admin_user_id": admin.id,
        "reviewer_user_id": reviewer.id,
        "general_user_id": general_user.id,
        "auditor_user_id": auditor.id,
        "outsider_user_id": outsider_user.id,
        "process_definition_id": definition.id,
    }


@pytest.fixture
def role_client_factory(client: TestClient, db_session: Session):
    def _factory(user_id: str) -> TestClient:
        def _override_current_user() -> str:
            return user_id

        # Import app here (delayed) so it exists in this scope and is configured
        from src.main import app
        # Also override org context to return the membership role for this user.
        # If the caller provided an X-Organization-Id header, enforce membership
        # for that specific organization so cross-org requests are rejected with
        # a membership error (403) instead of letting downstream lookup return 404.
        def _override_org_context_for_user(
            organization_id: str = Header(default="", alias="X-Organization-Id")
        ) -> tuple[str, str]:
            query = db_session.query(OrganizationMembership).filter(
                OrganizationMembership.user_id == user_id,
                OrganizationMembership.status == MembershipStatus.ACTIVE,
            )
            if organization_id != "":
                query = query.filter(OrganizationMembership.organization_id == organization_id)

            membership = query.first()
            if membership is None:
                raise ForbiddenError("User is not an active member of the requested organization")
            return (membership.organization_id, membership.role_name.value)

        app.dependency_overrides[get_current_user_id] = _override_current_user
        app.dependency_overrides[get_current_org_context] = _override_org_context_for_user
        return client

    return _factory
