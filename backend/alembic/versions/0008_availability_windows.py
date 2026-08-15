"""availability_windows

Revision ID: 0008_availability_windows
Revises: 0007_job_requirements
Create Date: 2026-08-14

spec Part D.4, exact. No team_id, no is_recurring, no recurrence_rule.
Index (worker_profile_id, start_time, end_time) per spec's explicit
"Index:" note.
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PGUUID

revision: str = "0008_availability_windows"
down_revision: Union[str, None] = "0007_job_requirements"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "availability_windows",
        sa.Column("id", PGUUID(as_uuid=True), primary_key=True),
        sa.Column(
            "worker_profile_id",
            PGUUID(as_uuid=True),
            sa.ForeignKey("worker_profiles.id"),
            nullable=False,
        ),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "end_time > start_time", name="ck_availability_windows_valid_time_range"
        ),
    )
    op.create_index(
        "ix_availability_windows_worker_start_end",
        "availability_windows",
        ["worker_profile_id", "start_time", "end_time"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_availability_windows_worker_start_end", table_name="availability_windows"
    )
    op.drop_table("availability_windows")
