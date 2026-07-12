"""add_available_hours_per_week

Revision ID: 5a5c9e2b1156
Revises: 4f15d3899166
Create Date: 2026-07-08 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5a5c9e2b1156'
down_revision: Union[str, None] = '4f15d3899166'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('student_preferences', sa.Column('available_hours_per_week', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('student_preferences', 'available_hours_per_week')
