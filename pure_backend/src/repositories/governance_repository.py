"""Provide persistence operations for governance data and maintenance jobs."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.enums import JobStatus
from src.models.governance import (
    DataDictionary,
    DataImportBatch,
    DataImportBatchDetail,
    DataSnapshot,
    SchedulerJobRecord,
)


class GovernanceRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_import_batch(self, batch: DataImportBatch) -> DataImportBatch:
        self.session.add(batch)
        self.session.flush()
        return batch

    def add_import_details(self, details: list[DataImportBatchDetail]) -> None:
        self.session.add_all(details)
        self.session.flush()

    def create_snapshot(self, snapshot: DataSnapshot) -> DataSnapshot:
        self.session.add(snapshot)
        self.session.flush()
        return snapshot

    def latest_snapshot_for_domain(self, organization_id: str, domain: str) -> DataSnapshot | None:
        stmt = (
            select(DataSnapshot)
            .where(
                DataSnapshot.organization_id == organization_id,
                DataSnapshot.domain == domain,
            )
            .order_by(DataSnapshot.version.desc())
            .limit(1)
        )
        return self.session.scalar(stmt)

    def get_snapshot(self, organization_id: str, snapshot_id: str) -> DataSnapshot | None:
        stmt = select(DataSnapshot).where(
            DataSnapshot.id == snapshot_id,
            DataSnapshot.organization_id == organization_id,
        )
        return self.session.scalar(stmt)

    def list_snapshots(self, organization_id: str, domain: str) -> list[DataSnapshot]:
        stmt = select(DataSnapshot).where(
            DataSnapshot.organization_id == organization_id,
            DataSnapshot.domain == domain,
        )
        return list(self.session.scalars(stmt))

    def create_job_record(self, job: SchedulerJobRecord) -> SchedulerJobRecord:
        self.session.add(job)
        self.session.flush()
        return job

    def list_due_jobs(self, now: datetime, organization_id: str | None = None) -> list[SchedulerJobRecord]:
        stmt = select(SchedulerJobRecord).where(
            SchedulerJobRecord.status == JobStatus.PENDING,
            SchedulerJobRecord.next_run_at.is_not(None),
            SchedulerJobRecord.next_run_at <= now,
        )
        if organization_id is not None:
            stmt = stmt.where(SchedulerJobRecord.organization_id == organization_id)
        return list(self.session.scalars(stmt))

    def get_data_dictionaries(self, organization_id: str, domain: str | None = None) -> list[DataDictionary]:
        stmt = select(DataDictionary).where(DataDictionary.organization_id == organization_id)
        if domain:
            stmt = stmt.where(DataDictionary.domain == domain)
        return list(self.session.scalars(stmt))

    def create_data_dictionary(self, dd: DataDictionary) -> DataDictionary:
        self.session.add(dd)
        self.session.flush()
        return dd

    def get_data_dictionary(self, organization_id: str, dd_id: str) -> DataDictionary | None:
        stmt = select(DataDictionary).where(
            DataDictionary.id == dd_id,
            DataDictionary.organization_id == organization_id,
        )
        return self.session.scalar(stmt)

    def update_data_dictionary(self, dd: DataDictionary) -> DataDictionary:
        self.session.merge(dd)
        self.session.flush()
        return dd

    def delete_data_dictionary(self, dd: DataDictionary) -> None:
        self.session.delete(dd)
        self.session.flush()
