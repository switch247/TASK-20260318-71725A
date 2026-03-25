from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base
from src.models.common import TimestampMixin, UuidPrimaryKeyMixin
from src.models.enums import ExportStatus


class OperationalMetricSnapshot(Base, UuidPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "operational_metric_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "metric_code",
            "snapshot_at",
            name="uq_metric_snapshots_org_metric_time",
        ),
    )

    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    metric_code: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    snapshot_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    metric_value: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    dimensions_json: Mapped[str | None] = mapped_column(Text, nullable=True)


class ReportDefinition(Base, UuidPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "report_definitions"

    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    resource: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    filters_json: Mapped[str] = mapped_column(Text, nullable=False)
    selected_fields_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_by_user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )


class ExportTask(Base, UuidPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "export_tasks"

    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    requested_by_user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    resource: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    field_whitelist_json: Mapped[str] = mapped_column(Text, nullable=False)
    desensitization_policy_json: Mapped[str] = mapped_column(Text, nullable=False)
    query_filters_json: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[ExportStatus] = mapped_column(
        Enum(ExportStatus), nullable=False, default=ExportStatus.PENDING, index=True
    )
    trace_code: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    result_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )


class ExportTaskRecord(Base, UuidPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "export_task_records"

    export_task_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("export_tasks.id", ondelete="CASCADE"), index=True
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    event_payload_json: Mapped[str] = mapped_column(Text, nullable=False)
