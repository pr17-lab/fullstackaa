"""add_security_fields_to_users

Revision ID: 47cc3a33fc7d
Revises: 78fc2c08ba84
Create Date: 2026-01-19 09:41:29.149777

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '47cc3a33fc7d'
down_revision: Union[str, None] = '78fc2c08ba84'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None



def upgrade() -> None:
    # Add security fields to users table
    op.add_column('users', sa.Column('failed_login_attempts', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('users', sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    # Remove security fields from users table
    op.drop_column('users', 'locked_until')
    op.drop_column('users', 'failed_login_attempts')

