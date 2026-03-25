from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from src.models.enums import MembershipStatus, RoleName, WorkflowType
from src.models.identity import Organization, OrganizationMembership, User
from src.models.medical_ops import Appointment, Doctor, Expense, Patient
from src.models.operations import OperationalMetricSnapshot
from src.models.process import ProcessDefinition
from src.services.crypto_service import encrypt_sensitive, hash_password
from src.services.seed_service import seed_role_permissions


def seed_demo_dataset(session: Session) -> dict[str, str]:
    seed_role_permissions(session)

    organization = Organization(code="DEMO-HOSP", name="Demo Hospital", is_active=True)
    session.add(organization)
    session.flush()

    admin_user = User(
        username="admin_demo",
        password_hash=hash_password("Admin1234"),
        display_name="Demo Admin",
        email="admin@demo.local",
        phone_encrypted=encrypt_sensitive("13900001111"),
        id_number_encrypted=encrypt_sensitive("110101198001011234"),
    )
    reviewer_user = User(
        username="reviewer_demo",
        password_hash=hash_password("Review1234"),
        display_name="Demo Reviewer",
        email="reviewer@demo.local",
    )
    general_user = User(
        username="user_demo",
        password_hash=hash_password("User12345"),
        display_name="Demo User",
        email="user@demo.local",
    )
    auditor_user = User(
        username="auditor_demo",
        password_hash=hash_password("Audit12345"),
        display_name="Demo Auditor",
        email="auditor@demo.local",
    )
    session.add_all([admin_user, reviewer_user, general_user, auditor_user])
    session.flush()

    session.add_all(
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
                organization_id=organization.id,
                user_id=auditor_user.id,
                role_name=RoleName.AUDITOR,
                status=MembershipStatus.ACTIVE,
            ),
        ]
    )

    process_definition = ProcessDefinition(
        organization_id=organization.id,
        name="Resource Allocation Workflow",
        workflow_type=WorkflowType.RESOURCE_APPLICATION,
        version=1,
        is_active=True,
        definition_json='{"nodes":[{"key":"review-node-1","type":"approval"}]}',
    )
    session.add(process_definition)

    patient = Patient(
        organization_id=organization.id,
        patient_number="P-1001",
        name="Alice Patient",
        contact_encrypted=encrypt_sensitive("13800002222"),
    )
    doctor = Doctor(
        organization_id=organization.id,
        doctor_number="D-1001",
        name="Bob Doctor",
        department="Cardiology",
    )
    session.add_all([patient, doctor])
    session.flush()

    appointment = Appointment(
        organization_id=organization.id,
        patient_id=patient.id,
        doctor_id=doctor.id,
        scheduled_at=datetime.now(UTC) + timedelta(days=1),
        status="scheduled",
        anomaly_flag=None,
    )
    expense = Expense(
        organization_id=organization.id,
        patient_id=patient.id,
        doctor_id=doctor.id,
        expense_type="consultation",
        amount=120.5,
    )
    metric_1 = OperationalMetricSnapshot(
        organization_id=organization.id,
        metric_code="activity",
        snapshot_at=datetime.now(UTC) - timedelta(hours=1),
        metric_value=80.0,
        dimensions_json='{"department":"Cardiology"}',
    )
    metric_2 = OperationalMetricSnapshot(
        organization_id=organization.id,
        metric_code="message_reach",
        snapshot_at=datetime.now(UTC) - timedelta(hours=2),
        metric_value=62.0,
        dimensions_json='{"channel":"sms"}',
    )
    metric_3 = OperationalMetricSnapshot(
        organization_id=organization.id,
        metric_code="attendance_anomaly",
        snapshot_at=datetime.now(UTC) - timedelta(hours=3),
        metric_value=3.0,
        dimensions_json='{"severity":"medium"}',
    )
    metric_4 = OperationalMetricSnapshot(
        organization_id=organization.id,
        metric_code="work_order_sla",
        snapshot_at=datetime.now(UTC) - timedelta(hours=4),
        metric_value=97.0,
        dimensions_json='{"window":"24h"}',
    )
    session.add_all([appointment, expense, metric_1, metric_2, metric_3, metric_4])

    session.commit()

    return {
        "organization_id": organization.id,
        "admin_user_id": admin_user.id,
        "reviewer_user_id": reviewer_user.id,
        "general_user_id": general_user.id,
        "auditor_user_id": auditor_user.id,
        "process_definition_id": process_definition.id,
        "patient_id": patient.id,
        "doctor_id": doctor.id,
    }
