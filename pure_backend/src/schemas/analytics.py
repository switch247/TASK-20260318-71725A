from datetime import datetime

from pydantic import BaseModel, Field


class MetricsQuery(BaseModel):
    from_time: datetime
    to_time: datetime
    metric_codes: list[str] = Field(default_factory=list)


class CreateReportRequest(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    resource: str = Field(min_length=2, max_length=100)
    filters_json: str
    selected_fields_json: str


class CreateExportTaskRequest(BaseModel):
    resource: str = Field(min_length=2, max_length=100)
    field_whitelist_json: str
    desensitization_policy_json: str
    query_filters_json: str


class ExportPreviewRow(BaseModel):
    values: dict[str, str]


class ExportPreviewRequest(BaseModel):
    field_whitelist_json: str
    desensitization_policy_json: str
    rows: list[ExportPreviewRow]
