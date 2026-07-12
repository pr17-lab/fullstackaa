"""add_last_reviewed_at_to_job_requirements

Revision ID: 2b3c4d5e6f7a
Revises: 5a5c9e2b1156
Create Date: 2026-07-08 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2b3c4d5e6f7a'
down_revision: Union[str, None] = '5a5c9e2b1156'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('job_skill_requirements', sa.Column('last_reviewed_at', sa.DateTime(timezone=True), nullable=True))
    op.execute("UPDATE job_skill_requirements SET last_reviewed_at = '2026-03-01 00:00:00+00:00'")


def downgrade() -> None:
    op.drop_column('job_skill_requirements', 'last_reviewed_at')
