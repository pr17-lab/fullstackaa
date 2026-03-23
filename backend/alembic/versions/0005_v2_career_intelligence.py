"""v2 career intelligence

Revision ID: 0005
Revises: 0004
Create Date: 2026-03-23 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0006_v2_career_intelligence'
down_revision = '0005_new_dataset_columns'
branch_labels = None
depends_on = None


def upgrade():
    # 1. skill_taxonomy
    op.create_table(
        'skill_taxonomy',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('skill_name', sa.String(length=100), unique=True, nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('aliases', postgresql.ARRAY(sa.Text())),
        sa.Column('description', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # 2. student_projects
    op.create_table(
        'student_projects',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('tech_stack', postgresql.ARRAY(sa.Text())),
        sa.Column('domain', sa.String(length=100)),
        sa.Column('complexity', sa.String(length=20)),
        sa.Column('project_url', sa.String(length=500)),
        sa.Column('completed_at', sa.Date()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # 3. student_preferences
    op.create_table(
        'student_preferences',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('target_roles', postgresql.ARRAY(sa.Text())),
        sa.Column('preferred_domains', postgresql.ARRAY(sa.Text())),
        sa.Column('open_to_remote', sa.Boolean(), server_default='true'),
        sa.Column('career_transition', sa.Boolean(), server_default='false'),
        sa.Column('transition_from', sa.String(length=100)),
        sa.Column('transition_to', sa.String(length=100)),
        sa.Column('timeline_months', sa.Integer()),
        sa.Column('experience_level', sa.String(length=20)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # 4. student_skills
    op.create_table(
        'student_skills',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('skill_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('skill_taxonomy.id'), nullable=False),
        sa.Column('confidence_score', sa.Numeric(precision=5, scale=2), server_default='0'),
        sa.Column('level', sa.String(length=20)),
        sa.Column('source', postgresql.ARRAY(sa.Text())),
        sa.Column('academic_weight', sa.Numeric(precision=5, scale=2), server_default='0'),
        sa.Column('project_weight', sa.Numeric(precision=5, scale=2), server_default='0'),
        sa.Column('behavior_weight', sa.Numeric(precision=5, scale=2), server_default='0'),
        sa.Column('last_computed_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.UniqueConstraint('user_id', 'skill_id', name='uq_user_skill')
    )

    # 5. job_skill_requirements
    op.create_table(
        'job_skill_requirements',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('job_role', sa.String(length=255), nullable=False),
        sa.Column('skill_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('skill_taxonomy.id'), nullable=False),
        sa.Column('importance', sa.String(length=20), nullable=False),
        sa.Column('min_score_required', sa.Numeric(precision=5, scale=2)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.UniqueConstraint('job_role', 'skill_id', name='uq_job_role_skill')
    )

    # 6. skill_gaps
    op.create_table(
        'skill_gaps',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('job_role', sa.String(length=255), nullable=False),
        sa.Column('match_score', sa.Numeric(precision=5, scale=2)),
        sa.Column('missing_skills', postgresql.JSONB()),
        sa.Column('weak_skills', postgresql.JSONB()),
        sa.Column('strong_skills', postgresql.JSONB()),
        sa.Column('computed_at', sa.DateTime(timezone=True)),
        sa.UniqueConstraint('user_id', 'job_role', name='uq_user_gap_job_role')
    )

    # 7. roadmaps
    op.create_table(
        'roadmaps',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('job_role', sa.String(length=255), nullable=False),
        sa.Column('version', sa.Integer(), server_default='1'),
        sa.Column('status', sa.String(length=20), server_default="'active'"),
        sa.Column('is_transition', sa.Boolean(), server_default='false'),
        sa.Column('generated_by', sa.String(length=20)),
        sa.Column('total_tasks', sa.Integer(), server_default='0'),
        sa.Column('completed_tasks', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # 8. roadmap_tasks
    op.create_table(
        'roadmap_tasks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('roadmap_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('roadmaps.id', ondelete='CASCADE'), nullable=False),
        sa.Column('skill_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('skill_taxonomy.id'), nullable=True),
        sa.Column('phase', sa.String(length=20), nullable=False),
        sa.Column('task_type', sa.String(length=30)),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('resource_url', sa.String(length=500)),
        sa.Column('platform', sa.String(length=100)),
        sa.Column('estimated_hours', sa.Integer()),
        sa.Column('order_index', sa.Integer()),
        sa.Column('status', sa.String(length=20), server_default="'pending'"),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
        sa.Column('feedback_score', sa.SmallInteger()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # 9. job_cache
    op.create_table(
        'job_cache',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('query_key', sa.String(length=255), unique=True, nullable=False),
        sa.Column('job_title', sa.String(length=255)),
        sa.Column('source', sa.String(length=50)),
        sa.Column('raw_results', postgresql.JSONB()),
        sa.Column('job_count', sa.Integer()),
        sa.Column('fetched_at', sa.DateTime(timezone=True)),
        sa.Column('expires_at', sa.DateTime(timezone=True)),
    )

    # 10. behavior_summary
    op.create_table(
        'behavior_summary',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('interviews_completed', sa.Integer(), server_default='0'),
        sa.Column('interviews_abandoned', sa.Integer(), server_default='0'),
        sa.Column('questions_answered', sa.Integer(), server_default='0'),
        sa.Column('roadmap_tasks_done', sa.Integer(), server_default='0'),
        sa.Column('login_streak_days', sa.Integer(), server_default='0'),
        sa.Column('last_active_at', sa.DateTime(timezone=True)),
        sa.Column('consistency_score', sa.Numeric(precision=5, scale=2), server_default='0'),
        sa.Column('engagement_level', sa.String(length=20)),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )


def downgrade():
    # Drop tables in reverse order of creation
    op.drop_table('behavior_summary')
    op.drop_table('job_cache')
    op.drop_table('roadmap_tasks')
    op.drop_table('roadmaps')
    op.drop_table('skill_gaps')
    op.drop_table('job_skill_requirements')
    op.drop_table('student_skills')
    op.drop_table('student_preferences')
    op.drop_table('student_projects')
    op.drop_table('skill_taxonomy')
