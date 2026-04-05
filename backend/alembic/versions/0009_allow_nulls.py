"""Allow nullable values in academic term gpa and marks

Revision ID: 0009_allow_nullable_academic_records
Revises: 0008_interview_evaluation
Create Date: 2026-03-29
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0009_allow_nulls'
down_revision: Union[str, None] = '0008_interview_evaluation'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Alter academic_terms.gpa to be nullable
    op.alter_column('academic_terms', 'gpa',
               existing_type=sa.NUMERIC(precision=3, scale=2),
               nullable=True)
               
    # Alter subjects properties to be nullable
    op.alter_column('subjects', 'marks',
               existing_type=sa.NUMERIC(precision=5, scale=2),
               nullable=True)
    op.alter_column('subjects', 'grade',
               existing_type=sa.VARCHAR(length=2),
               nullable=True)
               
    # pass_fail was already nullable from migration 0005, but we can ensure it here
    op.alter_column('subjects', 'pass_fail',
               existing_type=sa.VARCHAR(length=4),
               nullable=True)


def downgrade() -> None:
    op.alter_column('subjects', 'pass_fail',
               existing_type=sa.VARCHAR(length=4),
               nullable=True)
    op.alter_column('subjects', 'grade',
               existing_type=sa.VARCHAR(length=2),
               nullable=False)
    op.alter_column('subjects', 'marks',
               existing_type=sa.NUMERIC(precision=5, scale=2),
               nullable=False)
               
    op.alter_column('academic_terms', 'gpa',
               existing_type=sa.NUMERIC(precision=3, scale=2),
               nullable=False)
