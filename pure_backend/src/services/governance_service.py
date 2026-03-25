import json
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from src.core.errors import NotFoundError, ValidationError
from src.models.enums import ImportStatus, JobStatus
from src.models.governance import (
    DataImportBatch,
    DataImportBatchDetail,
    DataSnapshot,
    SchedulerJobRecord,
)
from src.repositories.governance_repository import GovernanceRepository
from src.schemas.governance import CreateImportBatchRequest, CreateSnapshotRequest


class GovernanceService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = GovernanceRepository(session)

    def create_import_batch(
        self,
        organization_id: str,
        user_id: str,
        request: CreateImportBatchRequest,
    ) -> dict[str, object]:
        batch = DataImportBatch(
            organization_id=organization_id,
            requested_by_user_id=user_id,
            source_file_path=request.source_file_path,
            status=ImportStatus.VALIDATING,
            total_rows=len(request.rows),
            success_rows=0,
            failed_rows=0,
        )
        self.repository.create_import_batch(batch)

        details: list[DataImportBatchDetail] = []
        seen_payloads: set[str] = set()
        success_count = 0
        failed_count = 0

        for row in request.rows:
            error_message = self._validate_import_row(row.payload_json, seen_payloads)
            if error_message is None:
                success_count += 1
            else:
                failed_count += 1

            details.append(
                DataImportBatchDetail(
                    batch_id=batch.id,
                    row_number=row.row_number,
                    row_payload_json=row.payload_json,
                    error_message=error_message,
                )
            )

        batch.success_rows = success_count
        batch.failed_rows = failed_count
        batch.status = ImportStatus.SUCCEEDED if failed_count == 0 else ImportStatus.FAILED

        self.repository.add_import_details(details)
        self.session.commit()

        return {
            "batch_id": batch.id,
            "status": batch.status.value,
            "total_rows": batch.total_rows,
            "success_rows": batch.success_rows,
            "failed_rows": batch.failed_rows,
        }

    def create_snapshot(
        self, organization_id: str, request: CreateSnapshotRequest
    ) -> dict[str, str | int]:
        json.loads(request.snapshot_payload_json)

        snapshot = DataSnapshot(
            organization_id=organization_id,
            domain=request.domain,
            version=request.version,
            snapshot_payload_json=request.snapshot_payload_json,
            lineage_from_snapshot_id=request.lineage_from_snapshot_id,
        )
        self.repository.create_snapshot(snapshot)
        self.session.commit()
        return {"snapshot_id": snapshot.id, "domain": snapshot.domain, "version": snapshot.version}

    def rollback_snapshot(self, organization_id: str, snapshot_id: str) -> dict[str, str]:
        snapshot = self.repository.get_snapshot(organization_id, snapshot_id)
        if snapshot is None:
            raise NotFoundError("Snapshot not found")

        self.session.commit()
        return {"snapshot_id": snapshot.id, "status": "rolled_back"}

    def schedule_maintenance_jobs(self) -> list[dict[str, object]]:
        now = datetime.utcnow()
        jobs = [
            SchedulerJobRecord(
                organization_id=None,
                job_type="daily_full_backup",
                status=JobStatus.PENDING,
                retry_count=0,
                max_retries=3,
                next_run_at=now + timedelta(days=1),
                last_error=None,
            ),
            SchedulerJobRecord(
                organization_id=None,
                job_type="archive_30_day_records",
                status=JobStatus.PENDING,
                retry_count=0,
                max_retries=3,
                next_run_at=now + timedelta(days=1),
                last_error=None,
            ),
        ]
        for job in jobs:
            self.repository.create_job_record(job)
        self.session.commit()
        return [
            {"job_id": job.id, "job_type": job.job_type, "max_retries": job.max_retries}
            for job in jobs
        ]

    def _validate_import_row(self, payload_json: str, seen_payloads: set[str]) -> str | None:
        if payload_json.strip() == "":
            return "missing_payload"

        try:
            data = json.loads(payload_json)
        except json.JSONDecodeError as exc:
            raise ValidationError("Import row is not valid JSON") from exc

        fingerprint = json.dumps(data, sort_keys=True)
        if fingerprint in seen_payloads:
            return "duplicate_row"

        seen_payloads.add(fingerprint)

        if isinstance(data, dict) and "value" in data:
            value = data["value"]
            if isinstance(value, (int, float)) and (value < 0 or value > 1_000_000):
                return "out_of_bounds"

        return None
