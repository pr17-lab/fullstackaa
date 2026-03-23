"""add subjects unique constraint

Revision ID: a5672fe570cf
Revises: 0006_add_cgpa_10scale
Create Date: 2026-03-23 21:08:57.520514

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a5672fe570cf'
down_revision: Union[str, None] = '0006_add_cgpa_10scale'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add unique constraint on term_id and subject_code to subjects table
    op.create_unique_constraint(
        'uq_subjects_term_subject_code',
        'subjects',
        ['term_id', 'subject_code']
    )


def downgrade() -> None:
    # Drop the unique constraint
    op.drop_constraint(
        'uq_subjects_term_subject_code',
        'subjects',
        type_='unique'
    )
