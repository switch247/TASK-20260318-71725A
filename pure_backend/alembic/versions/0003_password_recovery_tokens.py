"""Add password recovery token table with compatibility checks.

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


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def _index_exists(table_name: str, index_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    indexes = inspector.get_indexes(table_name)
    return any(idx.get("name") == index_name for idx in indexes)


def _create_index_if_missing(index_name: str, table_name: str, columns: list[str]) -> None:
    if not _index_exists(table_name, index_name):
        op.create_index(index_name, table_name, columns)


def _drop_index_if_exists(index_name: str, table_name: str) -> None:
    if _index_exists(table_name, index_name):
        op.drop_index(index_name, table_name=table_name)


def upgrade() -> None:
    if not _table_exists("password_recovery_tokens"):
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

    _create_index_if_missing("ix_password_recovery_tokens_user_id", "password_recovery_tokens", ["user_id"])
    _create_index_if_missing(
        "ix_password_recovery_tokens_expires_at",
        "password_recovery_tokens",
        ["expires_at"],
    )
    _create_index_if_missing("ix_password_recovery_tokens_used_at", "password_recovery_tokens", ["used_at"])


def downgrade() -> None:
    if _table_exists("password_recovery_tokens"):
        _drop_index_if_exists("ix_password_recovery_tokens_used_at", "password_recovery_tokens")
        _drop_index_if_exists("ix_password_recovery_tokens_expires_at", "password_recovery_tokens")
        _drop_index_if_exists("ix_password_recovery_tokens_user_id", "password_recovery_tokens")
        op.drop_table("password_recovery_tokens")
