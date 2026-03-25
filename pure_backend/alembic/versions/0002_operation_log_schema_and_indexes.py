"""Add operation log structured fields and hot-path indexes.

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


def upgrade() -> None:
    op.add_column("operation_logs", sa.Column("operation", sa.String(length=100), nullable=True))
    op.add_column(
        "operation_logs", sa.Column("resource_type", sa.String(length=100), nullable=True)
    )
    op.add_column("operation_logs", sa.Column("trace_id", sa.String(length=100), nullable=True))
    op.add_column("operation_logs", sa.Column("before_json", sa.Text(), nullable=True))
    op.add_column("operation_logs", sa.Column("after_json", sa.Text(), nullable=True))
    op.add_column(
        "operation_logs", sa.Column("event_timestamp", sa.String(length=64), nullable=True)
    )

    op.create_index("ix_operation_logs_operation", "operation_logs", ["operation"])
    op.create_index("ix_operation_logs_resource_type", "operation_logs", ["resource_type"])
    op.create_index("ix_operation_logs_trace_id", "operation_logs", ["trace_id"])
    op.create_index("ix_operation_logs_event_timestamp", "operation_logs", ["event_timestamp"])
    op.create_index(
        "ix_operation_logs_org_created_at",
        "operation_logs",
        ["organization_id", "created_at"],
    )

    op.create_index(
        "ix_process_instances_org_business_submitted_at",
        "process_instances",
        ["organization_id", "business_number", "submitted_at"],
    )
    op.create_index(
        "ix_attachments_org_process",
        "attachments",
        ["organization_id", "process_instance_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_attachments_org_process", table_name="attachments")
    op.drop_index("ix_process_instances_org_business_submitted_at", table_name="process_instances")
    op.drop_index("ix_operation_logs_org_created_at", table_name="operation_logs")
    op.drop_index("ix_operation_logs_event_timestamp", table_name="operation_logs")
    op.drop_index("ix_operation_logs_trace_id", table_name="operation_logs")
    op.drop_index("ix_operation_logs_resource_type", table_name="operation_logs")
    op.drop_index("ix_operation_logs_operation", table_name="operation_logs")

    op.drop_column("operation_logs", "event_timestamp")
    op.drop_column("operation_logs", "after_json")
    op.drop_column("operation_logs", "before_json")
    op.drop_column("operation_logs", "trace_id")
    op.drop_column("operation_logs", "resource_type")
    op.drop_column("operation_logs", "operation")
