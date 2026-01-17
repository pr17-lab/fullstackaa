"""add_student_id_to_users

Revision ID: 78fc2c08ba84
Revises: c53fd9a60557
Create Date: 2026-01-16 10:43:08.099539

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '78fc2c08ba84'
down_revision: Union[str, None] = 'c53fd9a60557'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add student_id column as nullable first
    op.add_column('users', sa.Column('student_id', sa.String(length=50), nullable=True))
    
    # Create index on student_id
    op.create_index(op.f('ix_users_student_id'), 'users', ['student_id'], unique=True)
    
    # Note: student_id values should be populated using a separate data migration script
    # before making the column non-nullable
    # For now, we'll leave it nullable to allow existing users to continue functioning
    

def downgrade() -> None:
    # Drop index
    op.drop_index(op.f('ix_users_student_id'), table_name='users')
    
    # Drop column
    op.drop_column('users', 'student_id')
