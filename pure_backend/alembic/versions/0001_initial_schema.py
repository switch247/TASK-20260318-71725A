"""initial schema

Revision ID: 0001_initial_schema
Revises: None
Create Date: 2026-03-24
"""

from collections.abc import Sequence

import src.models  # noqa: F401
from alembic import op
from src.db.base import Base

# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
