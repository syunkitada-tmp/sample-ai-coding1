"""add_trace_id_to_jobs

Revision ID: a1b2c3d4e5f6
Revises: 6e145104e22a
Create Date: 2026-03-30

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "6e145104e22a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "jobs",
        sa.Column("trace_id", sa.String(length=36), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("jobs", "trace_id")
