"""Add password recovery token table.

Revision ID: 0003_password_recovery_tokens
Revises: 0002_operation_log_schema_and_indexes
Create Date: 2026-03-25
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003_password_recovery_tokens"
down_revision: str | None = "0002_operation_log_schema_and_indexes"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "password_recovery_tokens",
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("token_hash", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index("ix_password_recovery_tokens_user_id", "password_recovery_tokens", ["user_id"])
    op.create_index(
        "ix_password_recovery_tokens_expires_at",
        "password_recovery_tokens",
        ["expires_at"],
    )
    op.create_index("ix_password_recovery_tokens_used_at", "password_recovery_tokens", ["used_at"])


def downgrade() -> None:
    op.drop_index("ix_password_recovery_tokens_used_at", table_name="password_recovery_tokens")
    op.drop_index("ix_password_recovery_tokens_expires_at", table_name="password_recovery_tokens")
    op.drop_index("ix_password_recovery_tokens_user_id", table_name="password_recovery_tokens")
    op.drop_table("password_recovery_tokens")
