"""job_requirements

Revision ID: 0007_job_requirements
Revises: 0006_projects_and_locations
Create Date: 2026-08-14

spec Part D.5. workers_needed >= 1 and end_time > start_time enforced by
CHECK constraints. required_skills intentionally NOT implemented — see
app/models/job_requirement.py docstring; DEFERRED ARCHITECTURE ITEM.
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PGUUID

revision: str = "0007_job_requirements"
down_revision: Union[str, None] = "0006_projects_and_locations"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "job_requirements",
        sa.Column("id", PGUUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            PGUUID(as_uuid=True),
            sa.ForeignKey("projects.id"),
            nullable=False,
        ),
        sa.Column("workers_needed", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "workers_needed >= 1", name="ck_job_requirements_workers_needed_min"
        ),
        sa.CheckConstraint(
            "end_time > start_time", name="ck_job_requirements_valid_time_range"
        ),
    )
    op.create_index("ix_job_requirements_project_id", "job_requirements", ["project_id"])
    # Booking-window lookups by time range.
    op.create_index(
        "ix_job_requirements_start_end", "job_requirements", ["start_time", "end_time"]
    )


def downgrade() -> None:
    op.drop_index("ix_job_requirements_start_end", table_name="job_requirements")
    op.drop_index("ix_job_requirements_project_id", table_name="job_requirements")
    op.drop_table("job_requirements")
