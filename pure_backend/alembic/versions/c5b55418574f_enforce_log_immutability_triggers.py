"""enforce_log_immutability_triggers

Revision ID: c5b55418574f
Revises: 0003_password_recovery_tokens
Create Date: 2026-03-27 00:39:55.482983
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c5b55418574f'
down_revision: str | None = '0003_password_recovery_tokens'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # SQLite-specific triggers for DB-level immutability enforcement
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        op.execute("""
            CREATE TRIGGER operation_logs_no_update BEFORE UPDATE ON operation_logs
            BEGIN
                SELECT RAISE(FAIL, 'Updates not allowed on operation_logs');
            END;
        """)
        op.execute("""
            CREATE TRIGGER operation_logs_no_delete BEFORE DELETE ON operation_logs
            BEGIN
                SELECT RAISE(FAIL, 'Deletions not allowed on operation_logs');
            END;
        """)
        op.execute("""
            CREATE TRIGGER immutable_audit_logs_no_update BEFORE UPDATE ON immutable_audit_logs
            BEGIN
                SELECT RAISE(FAIL, 'Updates not allowed on immutable_audit_logs');
            END;
        """)
        op.execute("""
            CREATE TRIGGER immutable_audit_logs_no_delete BEFORE DELETE ON immutable_audit_logs
            BEGIN
                SELECT RAISE(FAIL, 'Deletions not allowed on immutable_audit_logs');
            END;
        """)


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        op.execute("DROP TRIGGER IF EXISTS operation_logs_no_update")
        op.execute("DROP TRIGGER IF EXISTS operation_logs_no_delete")
        op.execute("DROP TRIGGER IF EXISTS immutable_audit_logs_no_update")
        op.execute("DROP TRIGGER IF EXISTS immutable_audit_logs_no_delete")
