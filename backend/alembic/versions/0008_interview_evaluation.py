"""add interview evaluation columns

Revision ID: 0008_interview_evaluation
Revises: 0006_add_cgpa_10scale
Create Date: 2026-03-24 03:07:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0008_interview_evaluation'
down_revision = 'a5672fe570cf'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('interview_questions', sa.Column('ai_score', sa.SmallInteger(), nullable=True))
    op.add_column('interview_questions', sa.Column('ai_verdict', sa.String(length=20), nullable=True))
    op.add_column('interview_questions', sa.Column('ai_feedback', sa.Text(), nullable=True))
    op.add_column('interview_questions', sa.Column('model_answer', sa.Text(), nullable=True))
    op.add_column('interview_questions', sa.Column('evaluated_at', sa.TIMESTAMP(timezone=True), nullable=True))

def downgrade():
    op.drop_column('interview_questions', 'evaluated_at')
    op.drop_column('interview_questions', 'model_answer')
    op.drop_column('interview_questions', 'ai_feedback')
    op.drop_column('interview_questions', 'ai_verdict')
    op.drop_column('interview_questions', 'ai_score')
