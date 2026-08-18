"""add_missing_interview_session_columns

Add is_micro, associated_skill_id, and roadmap_task_id columns to
interview_sessions that exist in the ORM model but were missing
from the migration chain.

Revision ID: a1b2c3d4e5f6
Revises: 353ba9408210
Create Date: 2026-08-13 19:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '353ba9408210'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ---- interview_sessions missing columns ----
    op.add_column(
        'interview_sessions',
        sa.Column('is_micro', sa.Boolean(), nullable=True, server_default='false'),
    )
    op.add_column(
        'interview_sessions',
        sa.Column('associated_skill_id', sa.UUID(), nullable=True),
    )
    op.create_foreign_key(
        'fk_interview_sessions_associated_skill_id',
        'interview_sessions',
        'skill_taxonomy',
        ['associated_skill_id'],
        ['id'],
    )
    op.add_column(
        'interview_sessions',
        sa.Column('roadmap_task_id', sa.UUID(), nullable=True),
    )
    op.create_foreign_key(
        'fk_interview_sessions_roadmap_task_id',
        'interview_sessions',
        'roadmap_tasks',
        ['roadmap_task_id'],
        ['id'],
    )

    # ---- interview_questions missing columns ----
    op.add_column(
        'interview_questions',
        sa.Column('follow_up', sa.Text(), nullable=True),
    )
    op.add_column(
        'interview_questions',
        sa.Column('mistakes', JSONB(), nullable=True, server_default='[]'),
    )
    op.add_column(
        'interview_questions',
        sa.Column('improvement', sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('interview_questions', 'improvement')
    op.drop_column('interview_questions', 'mistakes')
    op.drop_column('interview_questions', 'follow_up')
    op.drop_constraint('fk_interview_sessions_roadmap_task_id', 'interview_sessions', type_='foreignkey')
    op.drop_column('interview_sessions', 'roadmap_task_id')
    op.drop_constraint('fk_interview_sessions_associated_skill_id', 'interview_sessions', type_='foreignkey')
    op.drop_column('interview_sessions', 'associated_skill_id')
    op.drop_column('interview_sessions', 'is_micro')
