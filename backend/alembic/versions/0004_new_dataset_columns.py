"""Add new columns to student_profiles and subjects, rename branch to department.

Revision ID: 0005_new_dataset_columns
Revises: 0004_interview_hardening
Create Date: 2026-03-22
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# ---------------------------------------------------------------------------
# Revision identifiers
# ---------------------------------------------------------------------------
revision: str = '0005_new_dataset_columns'
down_revision: Union[str, None] = '0004_interview_hardening'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add new columns to student_profiles
    op.add_column('student_profiles', sa.Column('batch_year', sa.Integer(), nullable=True))
    op.add_column('student_profiles', sa.Column('performance_status', sa.String(length=20), nullable=True))
    op.add_column('student_profiles', sa.Column('backlog_count', sa.Integer(), server_default='0', nullable=True))
    op.add_column('student_profiles', sa.Column('active_backlog', sa.Boolean(), server_default='false', nullable=True))
    op.add_column('student_profiles', sa.Column('cgpa', sa.Numeric(precision=4, scale=2), nullable=True))

    # 2. Add new columns to subjects
    op.add_column('subjects', sa.Column('pass_fail', sa.String(length=4), nullable=True))
    op.add_column('subjects', sa.Column('total_marks', sa.Integer(), server_default='100', nullable=True))

    # 3. Rename branch to department in student_profiles
    # Using op.alter_column with new_column_name handles the rename cleanly in Postgres
    op.alter_column('student_profiles', 'branch', new_column_name='department')


def downgrade() -> None:
    # 1. Rename department back to branch
    op.alter_column('student_profiles', 'department', new_column_name='branch')

    # 2. Drop columns from subjects
    op.drop_column('subjects', 'total_marks')
    op.drop_column('subjects', 'pass_fail')

    # 3. Drop columns from student_profiles
    op.drop_column('student_profiles', 'cgpa')
    op.drop_column('student_profiles', 'active_backlog')
    op.drop_column('student_profiles', 'backlog_count')
    op.drop_column('student_profiles', 'performance_status')
    op.drop_column('student_profiles', 'batch_year')
