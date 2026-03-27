"""Add operation-log indexes safely without assuming baseline column state.

Revision ID: 0002_operation_log_schema_and_indexes
Revises: 0001_initial_schema
Create Date: 2026-03-25
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002_operation_log_schema_and_indexes"
down_revision: str | None = "0001_initial_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _column_exists(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = inspector.get_columns(table_name)
    return any(col.get("name") == column_name for col in columns)


def _index_exists(table_name: str, index_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    indexes = inspector.get_indexes(table_name)
    return any(idx.get("name") == index_name for idx in indexes)


def _add_column_if_missing(table_name: str, column: sa.Column) -> None:
    if not _column_exists(table_name, str(column.name)):
        op.add_column(table_name, column)


def _drop_column_if_exists(table_name: str, column_name: str) -> None:
    if _column_exists(table_name, column_name):
        op.drop_column(table_name, column_name)


def _create_index_if_missing(index_name: str, table_name: str, columns: list[str]) -> None:
    if not _index_exists(table_name, index_name):
        op.create_index(index_name, table_name, columns)


def _drop_index_if_exists(index_name: str, table_name: str) -> None:
    if _index_exists(table_name, index_name):
        op.drop_index(index_name, table_name=table_name)


def upgrade() -> None:
    _add_column_if_missing("operation_logs", sa.Column("operation", sa.String(length=100), nullable=True))
    _add_column_if_missing(
        "operation_logs", sa.Column("resource_type", sa.String(length=100), nullable=True)
    )
    _add_column_if_missing("operation_logs", sa.Column("trace_id", sa.String(length=100), nullable=True))
    _add_column_if_missing("operation_logs", sa.Column("before_json", sa.Text(), nullable=True))
    _add_column_if_missing("operation_logs", sa.Column("after_json", sa.Text(), nullable=True))
    _add_column_if_missing(
        "operation_logs", sa.Column("event_timestamp", sa.String(length=64), nullable=True)
    )

    _create_index_if_missing("ix_operation_logs_operation", "operation_logs", ["operation"])
    _create_index_if_missing("ix_operation_logs_resource_type", "operation_logs", ["resource_type"])
    _create_index_if_missing("ix_operation_logs_trace_id", "operation_logs", ["trace_id"])
    _create_index_if_missing("ix_operation_logs_event_timestamp", "operation_logs", ["event_timestamp"])
    _create_index_if_missing(
        "ix_operation_logs_org_created_at",
        "operation_logs",
        ["organization_id", "created_at"],
    )

    _create_index_if_missing(
        "ix_process_instances_org_business_submitted_at",
        "process_instances",
        ["organization_id", "business_number", "submitted_at"],
    )
    _create_index_if_missing(
        "ix_attachments_org_process",
        "attachments",
        ["organization_id", "process_instance_id"],
    )


def downgrade() -> None:
    _drop_index_if_exists("ix_attachments_org_process", "attachments")
    _drop_index_if_exists("ix_process_instances_org_business_submitted_at", "process_instances")
    _drop_index_if_exists("ix_operation_logs_org_created_at", "operation_logs")
    _drop_index_if_exists("ix_operation_logs_event_timestamp", "operation_logs")
    _drop_index_if_exists("ix_operation_logs_trace_id", "operation_logs")
    _drop_index_if_exists("ix_operation_logs_resource_type", "operation_logs")
    _drop_index_if_exists("ix_operation_logs_operation", "operation_logs")

    _drop_column_if_exists("operation_logs", "event_timestamp")
    _drop_column_if_exists("operation_logs", "after_json")
    _drop_column_if_exists("operation_logs", "before_json")
    _drop_column_if_exists("operation_logs", "trace_id")
    _drop_column_if_exists("operation_logs", "resource_type")
    _drop_column_if_exists("operation_logs", "operation")
