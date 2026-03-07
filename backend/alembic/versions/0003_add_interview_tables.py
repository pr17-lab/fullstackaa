"""Add interview sessions and questions tables.

Revision ID: 0003_add_interview_tables
Revises: 47cc3a33fc7d
Create Date: 2026-02-24

Adds the interview_sessions and interview_questions tables that are
required by the Interview Module (Phase 2).  This migration runs after
the existing user/security chain and does NOT touch any existing tables.

Indexes
-------
- ix_interview_sessions_user_id          — simple lookup by owner
- ix_interview_sessions_user_id_created_at — composite for paginated list_sessions()
- ix_interview_questions_session_id      — FK traversal for question loading

Constraints
-----------
- ck_interview_sessions_status — DB-level guard against arbitrary status strings;
  only 'active', 'completed', 'abandoned' are accepted.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# ---------------------------------------------------------------------------
# Revision identifiers
# ---------------------------------------------------------------------------
revision: str = "0003_add_interview_tables"
down_revision: Union[str, None] = "47cc3a33fc7d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ---------------------------------------------------------------------------
# Upgrade — create interview tables with all indexes and constraints
# ---------------------------------------------------------------------------
def upgrade() -> None:
    # ------------------------------------------------------------------
    # interview_sessions
    # ------------------------------------------------------------------
    op.create_table(
        "interview_sessions",
        sa.Column("id",         sa.UUID(),                  nullable=False),
        sa.Column("user_id",    sa.UUID(),                  nullable=False),
        sa.Column("branch",     sa.String(length=100),      nullable=False),
        sa.Column("topic",      sa.String(length=100),      nullable=True),
        sa.Column("status",     sa.String(length=20),       nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Simple user_id lookup (for auth checks, existence tests)
    op.create_index("ix_interview_sessions_user_id", "interview_sessions", ["user_id"])

    # Composite index — ORDER BY created_at DESC in list_sessions() uses this,
    # turning a full-scan + sort into an index-only scan for large user histories.
    op.create_index(
        "ix_interview_sessions_user_id_created_at",
        "interview_sessions",
        ["user_id", "created_at"],
    )

    # DB-level status guard — rejects any value not in the allowed lifecycle set.
    # Mirrors SessionStatus.ALL in the ORM model; two layers of validation.
    op.create_check_constraint(
        "ck_interview_sessions_status",
        "interview_sessions",
        "status IN ('active', 'completed', 'abandoned')",
    )

    # ------------------------------------------------------------------
    # interview_questions
    # ------------------------------------------------------------------
    op.create_table(
        "interview_questions",
        sa.Column("id",          sa.UUID(),             nullable=False),
        sa.Column("session_id",  sa.UUID(),             nullable=False),
        sa.Column("topic",       sa.String(length=100), nullable=False),
        sa.Column("question",    sa.Text(),             nullable=False),
        sa.Column("difficulty",  sa.String(length=20),  nullable=False, server_default="medium"),
        sa.Column("source",      sa.String(length=50),  nullable=True),
        sa.Column("user_answer", sa.Text(),             nullable=True),
        sa.Column("created_at",  sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["session_id"], ["interview_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # FK-traversal index — loaded by joinedload() in every get_session() / list_sessions() call.
    op.create_index("ix_interview_questions_session_id", "interview_questions", ["session_id"])


# ---------------------------------------------------------------------------
# Downgrade — remove interview objects in reverse FK order
# ---------------------------------------------------------------------------
def downgrade() -> None:
    op.drop_index("ix_interview_questions_session_id", table_name="interview_questions")
    op.drop_table("interview_questions")

    op.drop_constraint("ck_interview_sessions_status", "interview_sessions", type_="check")
    op.drop_index("ix_interview_sessions_user_id_created_at", table_name="interview_sessions")
    op.drop_index("ix_interview_sessions_user_id", table_name="interview_sessions")
    op.drop_table("interview_sessions")
