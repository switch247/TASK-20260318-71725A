"""Implement governance data workflows with snapshot, rollback, and job execution semantics."""

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
from src.models.identity import Organization
from src.models.operations import ExportTask, OperationalMetricSnapshot, ReportDefinition
from src.models.process import ProcessInstance
from src.models.security import Attachment
from src.repositories.governance_repository import GovernanceRepository
from src.schemas.governance import CreateImportBatchRequest, CreateSnapshotRequest
from src.services.operation_logger import OperationLogger


class GovernanceService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = GovernanceRepository(session)
        self.operation_logger = OperationLogger(session)

    def create_import_batch(
        self,
        organization_id: str,
        user_id: str,
        request: CreateImportBatchRequest,
        trace_id: str | None = None,
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
        self.operation_logger.log(
            actor_id=user_id,
            organization_id=organization_id,
            resource_type="data_import_batch",
            resource_id=batch.id,
            operation="create",
            trace_id=trace_id,
            after={
                "status": batch.status.value,
                "total_rows": batch.total_rows,
                "failed_rows": batch.failed_rows,
            },
        )
        self.session.commit()

        return {
            "batch_id": batch.id,
            "status": batch.status.value,
            "total_rows": batch.total_rows,
            "success_rows": batch.success_rows,
            "failed_rows": batch.failed_rows,
        }

    def create_snapshot(
        self,
        organization_id: str,
        request: CreateSnapshotRequest,
        trace_id: str | None = None,
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
        self.operation_logger.log(
            actor_id=None,
            organization_id=organization_id,
            resource_type="data_snapshot",
            resource_id=snapshot.id,
            operation="create",
            trace_id=trace_id,
            after={"domain": snapshot.domain, "version": snapshot.version},
        )
        self.session.commit()
        return {"snapshot_id": snapshot.id, "domain": snapshot.domain, "version": snapshot.version}

    def rollback_snapshot(
        self, organization_id: str, snapshot_id: str, trace_id: str | None = None
    ) -> dict[str, str]:
        snapshot = self.repository.get_snapshot(organization_id, snapshot_id)
        if snapshot is None:
            raise NotFoundError("Snapshot not found")

        self.repository.create_snapshot(
            DataSnapshot(
                organization_id=organization_id,
                domain=snapshot.domain,
                version=snapshot.version + 1,
                snapshot_payload_json=snapshot.snapshot_payload_json,
                lineage_from_snapshot_id=snapshot.id,
            )
        )
        self.operation_logger.log(
            actor_id=None,
            organization_id=organization_id,
            resource_type="data_snapshot",
            resource_id=snapshot.id,
            operation="rollback",
            trace_id=trace_id,
            after={"status": "rolled_back"},
        )
        self.session.commit()
        return {"snapshot_id": snapshot.id, "status": "rolled_back"}

    def schedule_maintenance_jobs(self, trace_id: str | None = None) -> list[dict[str, object]]:
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
            self.operation_logger.log(
                actor_id=None,
                organization_id=job.organization_id,
                resource_type="scheduler_job",
                resource_id=job.id,
                operation="schedule",
                trace_id=trace_id,
                after={"job_type": job.job_type, "max_retries": job.max_retries},
            )
        self.session.commit()
        return [
            {"job_id": job.id, "job_type": job.job_type, "max_retries": job.max_retries}
            for job in jobs
        ]

    def execute_due_jobs(self, trace_id: str | None = None) -> dict[str, object]:
        now = datetime.utcnow()
        due_jobs = self.repository.list_due_jobs(now)
        succeeded_ids: list[str] = []
        failed_ids: list[str] = []

        for job in due_jobs:
            job.status = JobStatus.RUNNING
            self.session.flush()
            try:
                if job.last_error is not None and "force_failure" in job.last_error:
                    raise ValidationError("Forced scheduler failure for resilience testing")
                job_org_ids: list[str] = []
                if job.job_type == "daily_full_backup":
                    if job.organization_id is not None:
                        job_org_ids = [job.organization_id]
                    else:
                        job_org_ids = [org.id for org in self.session.query(Organization).all()]

                    if len(job_org_ids) == 0:
                        raise ValidationError("No organizations available for backup")

                    for organization_id in job_org_ids:
                        latest = self.repository.latest_snapshot_for_domain(
                            organization_id,
                            "system_backup",
                        )
                        next_version = 1 if latest is None else latest.version + 1
                        backup_payload = {
                            "generated_at": now.isoformat(),
                            "organization_id": organization_id,
                            "tables": {
                                "process_instances": self.session.query(ProcessInstance)
                                .filter(ProcessInstance.organization_id == organization_id)
                                .count(),
                                "attachments": self.session.query(Attachment)
                                .filter(Attachment.organization_id == organization_id)
                                .count(),
                                "report_definitions": self.session.query(ReportDefinition)
                                .filter(ReportDefinition.organization_id == organization_id)
                                .count(),
                                "export_tasks": self.session.query(ExportTask)
                                .filter(ExportTask.organization_id == organization_id)
                                .count(),
                                "metric_snapshots": self.session.query(OperationalMetricSnapshot)
                                .filter(OperationalMetricSnapshot.organization_id == organization_id)
                                .count(),
                            },
                        }
                        self.repository.create_snapshot(
                            DataSnapshot(
                                organization_id=organization_id,
                                domain="system_backup",
                                version=next_version,
                                snapshot_payload_json=json.dumps(backup_payload),
                                lineage_from_snapshot_id=None,
                            )
                        )
                elif job.job_type == "archive_30_day_records":
                    if job.organization_id is not None:
                        archive_org_id = job.organization_id
                    else:
                        fallback_org = self.session.query(Organization).first()
                        if fallback_org is None:
                            raise ValidationError("No organizations available for archive")
                        archive_org_id = fallback_org.id

                    latest_archive = self.repository.latest_snapshot_for_domain(
                        archive_org_id,
                        "archive_summary",
                    )
                    archive_version = 1 if latest_archive is None else latest_archive.version + 1
                    archive_cutoff = now - timedelta(days=30)
                    archived_candidates = (
                        self.session.query(ProcessInstance)
                        .filter(
                            ProcessInstance.organization_id == archive_org_id,
                            ProcessInstance.submitted_at <= archive_cutoff,
                        )
                        .count()
                    )
                    self.repository.create_snapshot(
                        DataSnapshot(
                            organization_id=archive_org_id,
                            domain="archive_summary",
                            version=archive_version,
                            snapshot_payload_json=json.dumps(
                                {
                                    "archive": "summarized",
                                    "retention_days": 30,
                                    "generated_at": now.isoformat(),
                                    "archive_candidates": archived_candidates,
                                    "mode": "dry_run_summary",
                                }
                            ),
                            lineage_from_snapshot_id=None,
                        )
                    )
                job.status = JobStatus.SUCCEEDED
                succeeded_ids.append(job.id)
                self.operation_logger.log(
                    actor_id=None,
                    organization_id=job.organization_id,
                    resource_type="scheduler_job",
                    resource_id=job.id,
                    operation="execute",
                    trace_id=trace_id,
                    after={"status": job.status.value},
                )
            except Exception as exc:
                job.retry_count += 1
                job.last_error = str(exc)
                if job.retry_count >= job.max_retries:
                    job.status = JobStatus.FAILED
                    failed_ids.append(job.id)
                else:
                    job.status = JobStatus.PENDING
                    job.next_run_at = now + timedelta(minutes=5)

        self.session.commit()
        return {
            "succeeded": len(succeeded_ids),
            "failed": len(failed_ids),
            "succeeded_job_ids": succeeded_ids,
            "failed_job_ids": failed_ids,
        }

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
