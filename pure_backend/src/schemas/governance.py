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
