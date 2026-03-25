from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base
from src.models.common import TimestampMixin, UuidPrimaryKeyMixin
from src.models.enums import ProcessStatus, TaskStatus, WorkflowType


class ProcessDefinition(Base, UuidPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "process_definitions"

    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    workflow_type: Mapped[WorkflowType] = mapped_column(
        Enum(WorkflowType), nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    definition_json: Mapped[str] = mapped_column(Text, nullable=False)


class ProcessInstance(Base, UuidPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "process_instances"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "idempotency_key", name="uq_process_instances_org_idempotency_key"
        ),
    )

    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    process_definition_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("process_definitions.id", ondelete="RESTRICT"),
        index=True,
    )
    requested_by_user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="RESTRICT"),
        index=True,
    )
    business_number: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    status: Mapped[ProcessStatus] = mapped_column(
        Enum(ProcessStatus), nullable=False, default=ProcessStatus.SUBMITTED, index=True
    )
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    final_result_json: Mapped[str | None] = mapped_column(Text, nullable=True)


class ProcessTaskAssignment(Base, UuidPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "process_task_assignments"

    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    process_instance_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("process_instances.id", ondelete="CASCADE"), index=True
    )
    assignee_user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    task_node_key: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    task_status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus), nullable=False, default=TaskStatus.PENDING, index=True
    )
    is_joint_sign: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_parallel: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)


class ProcessAuditTrail(Base, UuidPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "process_audit_trails"

    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    process_instance_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("process_instances.id", ondelete="CASCADE"), index=True
    )
    actor_user_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    event_payload_json: Mapped[str] = mapped_column(Text, nullable=False)
