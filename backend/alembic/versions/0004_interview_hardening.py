"""Add missing indexes and status constraint to interview_sessions.

Revision ID: 0004_interview_hardening
Revises: 0003_add_interview_tables
Create Date: 2026-02-24

Context
-------
Migration 0003_add_interview_tables created the interview_sessions and
interview_questions tables but omitted:
  1. The composite index (user_id, created_at) — needed for ordered,
     paginated list_sessions() queries to avoid full-table scans.
  2. The CHECK constraint on status — needed for DB-level enforcement
     of the allowed lifecycle values ('active', 'completed', 'abandoned').

Both are defined in the ORM model; this migration brings the live DB
into sync with the model definition.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# ---------------------------------------------------------------------------
# Revision identifiers
# ---------------------------------------------------------------------------
revision: str = "0004_interview_hardening"
down_revision: Union[str, None] = "0003_add_interview_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ---------------------------------------------------------------------------
# Upgrade
# ---------------------------------------------------------------------------
def upgrade() -> None:
    # 1. Composite index for paginated, ordered per-user session queries.
    #    list_sessions() orders by created_at DESC — without this, Postgres
    #    falls back to a sequential scan + sort on every call.
    op.create_index(
        "ix_interview_sessions_user_id_created_at",
        "interview_sessions",
        ["user_id", "created_at"],
        unique=False,
    )

    # 2. CHECK constraint — DB-level guard complementing the Python-side
    #    SessionStatus constants.  Rejects any INSERT/UPDATE that supplies
    #    a status value outside the three allowed lifecycle states.
    op.create_check_constraint(
        "ck_interview_sessions_status",
        "interview_sessions",
        "status IN ('active', 'completed', 'abandoned')",
    )


# ---------------------------------------------------------------------------
# Downgrade
# ---------------------------------------------------------------------------
def downgrade() -> None:
    op.drop_constraint(
        "ck_interview_sessions_status",
        "interview_sessions",
        type_="check",
    )
    op.drop_index(
        "ix_interview_sessions_user_id_created_at",
        table_name="interview_sessions",
    )
