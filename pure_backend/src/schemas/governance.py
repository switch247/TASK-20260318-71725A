from datetime import datetime

from pydantic import BaseModel, Field


class DataImportRow(BaseModel):
    row_number: int
    payload_json: str


class CreateImportBatchRequest(BaseModel):
    source_file_path: str = Field(min_length=3, max_length=500)
    rows: list[DataImportRow]


class CreateSnapshotRequest(BaseModel):
    domain: str = Field(min_length=2, max_length=100)
    version: int = Field(ge=1)
    snapshot_payload_json: str
    lineage_from_snapshot_id: str | None = None


class RollbackSnapshotRequest(BaseModel):
    snapshot_id: str


class DataDictionaryCreate(BaseModel):
    domain: str = Field(min_length=2, max_length=100)
    code: str = Field(min_length=1, max_length=100)
    label: str = Field(min_length=1, max_length=255)
    constraints_json: str | None = None


class DataDictionaryUpdate(BaseModel):
    label: str | None = Field(min_length=1, max_length=255, default=None)
    constraints_json: str | None = None


class DataDictionaryResponse(BaseModel):
    id: str
    organization_id: str
    domain: str
    code: str
    label: str
    constraints_json: str | None
    created_at: datetime
    updated_at: datetime
