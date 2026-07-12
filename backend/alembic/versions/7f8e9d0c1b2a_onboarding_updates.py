"""onboarding_updates

Revision ID: 7f8e9d0c1b2a
Revises: 2b3c4d5e6f7a
Create Date: 2026-07-08 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7f8e9d0c1b2a'
down_revision: Union[str, None] = '2b3c4d5e6f7a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('student_skills', sa.Column('is_interview_scored', sa.Boolean(), server_default='0', nullable=False))
    op.add_column('student_preferences', sa.Column('onboarding_step', sa.String(length=50), server_default='preferred_role_set', nullable=False))


def downgrade() -> None:
    op.drop_column('student_preferences', 'onboarding_step')
    op.drop_column('student_skills', 'is_interview_scored')
