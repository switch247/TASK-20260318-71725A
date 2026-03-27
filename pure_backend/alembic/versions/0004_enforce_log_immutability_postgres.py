"""enforce log immutability for postgres

Revision ID: 0004_enforce_log_immutability_postgres
Revises: c5b55418574f
Create Date: 2026-03-27 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0004_enforce_log_immutability_postgres"
down_revision = "c5b55418574f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        # create a trigger function that prevents UPDATE or DELETE
        op.execute(
            """
            CREATE OR REPLACE FUNCTION prevent_update_delete() RETURNS trigger AS $$
            BEGIN
                RAISE EXCEPTION 'Updates and deletions are not allowed on audit/operation logs';
            END;
            $$ LANGUAGE plpgsql;
            """
        )

        # add triggers to the tables we want to make append-only
        for tbl in ("operation_logs", "immutable_audit_logs"):
            op.execute(
                sa.text(
                    f"CREATE TRIGGER {tbl}_no_update_delete BEFORE UPDATE OR DELETE ON {tbl} FOR EACH ROW EXECUTE FUNCTION prevent_update_delete();"
                )
            )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        for tbl in ("operation_logs", "immutable_audit_logs"):
            op.execute(sa.text(f"DROP TRIGGER IF EXISTS {tbl}_no_update_delete ON {tbl};"))

        op.execute("DROP FUNCTION IF EXISTS prevent_update_delete();")
