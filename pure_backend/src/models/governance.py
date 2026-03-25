from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base
from src.models.common import TimestampMixin, UuidPrimaryKeyMixin
from src.models.enums import ImportStatus, JobStatus


class DataDictionary(Base, UuidPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "data_dictionaries"

    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    domain: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    constraints_json: Mapped[str | None] = mapped_column(Text, nullable=True)


class DataImportBatch(Base, UuidPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "data_import_batches"

    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    requested_by_user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    source_file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[ImportStatus] = mapped_column(
        Enum(ImportStatus), nullable=False, default=ImportStatus.PENDING, index=True
    )
    total_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    success_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class DataImportBatchDetail(Base, UuidPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "data_import_batch_details"

    batch_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("data_import_batches.id", ondelete="CASCADE"), index=True
    )
    row_number: Mapped[int] = mapped_column(Integer, nullable=False)
    row_payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)


class DataSnapshot(Base, UuidPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "data_snapshots"

    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    domain: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot_payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    lineage_from_snapshot_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("data_snapshots.id", ondelete="SET NULL"), nullable=True
    )


class SchedulerJobRecord(Base, UuidPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "scheduler_job_records"

    organization_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True
    )
    job_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus), nullable=False, default=JobStatus.PENDING, index=True
    )
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    next_run_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
