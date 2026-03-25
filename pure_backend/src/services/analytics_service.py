import json
from datetime import datetime
from uuid import uuid4

from sqlalchemy.orm import Session

from src.models.enums import ExportStatus
from src.models.operations import ExportTask, ExportTaskRecord, ReportDefinition
from src.repositories.analytics_repository import AnalyticsRepository
from src.schemas.analytics import CreateExportTaskRequest, CreateReportRequest, MetricsQuery
from src.services.masking_service import mask_value


class AnalyticsService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = AnalyticsRepository(session)

    def get_dashboard_metrics(self, organization_id: str, query: MetricsQuery) -> dict[str, object]:
        snapshots = self.repository.list_metrics(
            organization_id=organization_id,
            metric_codes=query.metric_codes,
            from_time=query.from_time,
            to_time=query.to_time,
        )

        items = [
            {
                "metric_code": snapshot.metric_code,
                "snapshot_at": snapshot.snapshot_at.isoformat(),
                "metric_value": float(snapshot.metric_value),
                "dimensions_json": snapshot.dimensions_json,
                "kpi_type": self._resolve_kpi_type(snapshot.metric_code),
            }
            for snapshot in snapshots
        ]
        total_count = len(items)
        start = (query.page - 1) * query.limit
        end = start + query.limit
        paged_items = items[start:end]
        return {
            "items": paged_items,
            "count": len(paged_items),
            "total_count": total_count,
            "page": query.page,
            "limit": query.limit,
        }

    def create_report(
        self,
        organization_id: str,
        user_id: str,
        request: CreateReportRequest,
    ) -> ReportDefinition:
        json.loads(request.filters_json)
        json.loads(request.selected_fields_json)

        report = ReportDefinition(
            organization_id=organization_id,
            name=request.name,
            resource=request.resource,
            filters_json=request.filters_json,
            selected_fields_json=request.selected_fields_json,
            created_by_user_id=user_id,
        )
        self.repository.create_report(report)
        self.session.commit()
        self.session.refresh(report)
        return report

    def create_export_task(
        self,
        organization_id: str,
        user_id: str,
        request: CreateExportTaskRequest,
    ) -> ExportTask:
        json.loads(request.field_whitelist_json)
        json.loads(request.desensitization_policy_json)
        json.loads(request.query_filters_json)

        trace_code = f"EXP-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:8]}"
        task = ExportTask(
            organization_id=organization_id,
            requested_by_user_id=user_id,
            resource=request.resource,
            field_whitelist_json=request.field_whitelist_json,
            desensitization_policy_json=request.desensitization_policy_json,
            query_filters_json=request.query_filters_json,
            status=ExportStatus.PENDING,
            trace_code=trace_code,
            result_path=None,
            finished_at=None,
        )
        self.repository.create_export_task(task)
        self.repository.add_export_record(
            ExportTaskRecord(
                export_task_id=task.id,
                event_type="export_task_created",
                event_payload_json=json.dumps(
                    {
                        "trace_code": trace_code,
                        "resource": request.resource,
                    }
                ),
            )
        )
        self.session.commit()
        self.session.refresh(task)
        return task

    def preview_desensitized_row(
        self,
        role_name: str,
        row: dict[str, str],
        desensitization_policy: dict[str, str],
    ) -> dict[str, str]:
        if role_name in {"administrator", "auditor"}:
            return row

        result: dict[str, str] = {}
        for key, value in row.items():
            strategy = desensitization_policy.get(key)
            result[key] = mask_value(value, strategy) if strategy is not None else value
        return result

    def preview_export_rows(
        self,
        role_name: str,
        field_whitelist: list[str],
        desensitization_policy: dict[str, str],
        rows: list[dict[str, str]],
    ) -> list[dict[str, str]]:
        filtered_rows: list[dict[str, str]] = []
        for row in rows:
            filtered = {key: value for key, value in row.items() if key in field_whitelist}
            filtered_rows.append(
                self.preview_desensitized_row(role_name, filtered, desensitization_policy)
            )
        return filtered_rows

    def _resolve_kpi_type(self, metric_code: str) -> str:
        known_kpi_codes = {
            "activity": "activity",
            "message_reach": "message_reach",
            "attendance_anomaly": "attendance_anomaly",
            "work_order_sla": "work_order_sla",
        }
        return known_kpi_codes.get(metric_code, "custom")
