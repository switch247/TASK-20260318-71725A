from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

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
