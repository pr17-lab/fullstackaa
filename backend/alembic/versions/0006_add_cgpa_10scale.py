"""add cgpa_10scale to student_profiles

Revision ID: 0006_add_cgpa_10scale
Revises: 0006_v2_career_intelligence
Create Date: 2026-03-23 01:56:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0006_add_cgpa_10scale'
down_revision = '0006_v2_career_intelligence'
branch_labels = None
depends_on = None


def upgrade():
    # Add the missing cgpa_10scale column
    op.add_column(
        'student_profiles',
        sa.Column('cgpa_10scale', sa.Numeric(precision=4, scale=2), nullable=True)
    )

    # Populate from the existing cgpa column immediately
    op.execute(
        "UPDATE student_profiles SET cgpa_10scale = cgpa WHERE cgpa IS NOT NULL"
    )


def downgrade():
    op.drop_column('student_profiles', 'cgpa_10scale')
