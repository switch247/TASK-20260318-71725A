from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.medical_ops import Appointment, Doctor, Expense, Patient
from src.models.operations import (
    ExportTask,
    ExportTaskRecord,
    OperationalMetricSnapshot,
    ReportDefinition,
)


class AnalyticsRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_metrics(
        self,
        organization_id: str,
        metric_codes: list[str],
        from_time: datetime,
        to_time: datetime,
    ) -> list[OperationalMetricSnapshot]:
        stmt = select(OperationalMetricSnapshot).where(
            OperationalMetricSnapshot.organization_id == organization_id,
            OperationalMetricSnapshot.snapshot_at >= from_time,
            OperationalMetricSnapshot.snapshot_at <= to_time,
        )
        if metric_codes:
            stmt = stmt.where(OperationalMetricSnapshot.metric_code.in_(metric_codes))
        return list(self.session.scalars(stmt))

    def create_report(self, report: ReportDefinition) -> ReportDefinition:
        self.session.add(report)
        self.session.flush()
        return report

    def create_export_task(self, export_task: ExportTask) -> ExportTask:
        self.session.add(export_task)
        self.session.flush()
        return export_task

    def add_export_record(self, export_record: ExportTaskRecord) -> None:
        self.session.add(export_record)
        self.session.flush()

    def get_export_task(self, organization_id: str, task_id: str) -> ExportTask | None:
        stmt = select(ExportTask).where(
            ExportTask.id == task_id,
            ExportTask.organization_id == organization_id,
        )
        return self.session.scalar(stmt)

    def list_export_tasks(self, organization_id: str, limit: int, offset: int) -> list[ExportTask]:
        stmt = (
            select(ExportTask)
            .where(ExportTask.organization_id == organization_id)
            .order_by(ExportTask.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.scalars(stmt))

    def list_resource_rows(
        self,
        organization_id: str,
        resource: str,
        query_filters: dict[str, object],
    ) -> list[dict[str, str]]:
        if resource == "appointments":
            stmt = select(Appointment).where(Appointment.organization_id == organization_id)
            status_filter = query_filters.get("status")
            if isinstance(status_filter, str) and status_filter != "":
                stmt = stmt.where(Appointment.status == status_filter)
            items = list(self.session.scalars(stmt))
            return [
                {
                    "id": item.id,
                    "patient_id": item.patient_id,
                    "doctor_id": item.doctor_id,
                    "scheduled_at": item.scheduled_at.isoformat(),
                    "status": item.status,
                    "anomaly_flag": item.anomaly_flag or "",
                }
                for item in items
            ]

        if resource == "patients":
            stmt = select(Patient).where(Patient.organization_id == organization_id)
            items = list(self.session.scalars(stmt))
            return [
                {
                    "id": item.id,
                    "patient_number": item.patient_number,
                    "name": item.name,
                }
                for item in items
            ]

        if resource == "doctors":
            stmt = select(Doctor).where(Doctor.organization_id == organization_id)
            items = list(self.session.scalars(stmt))
            return [
                {
                    "id": item.id,
                    "doctor_number": item.doctor_number,
                    "name": item.name,
                    "department": item.department,
                }
                for item in items
            ]

        if resource == "expenses":
            stmt = select(Expense).where(Expense.organization_id == organization_id)
            items = list(self.session.scalars(stmt))
            return [
                {
                    "id": item.id,
                    "expense_type": item.expense_type,
                    "amount": str(item.amount),
                    "patient_id": item.patient_id or "",
                    "doctor_id": item.doctor_id or "",
                }
                for item in items
            ]

        return []
