"""bookings

Revision ID: 0009_bookings
Revises: 0008_availability_windows
Create Date: 2026-08-14

spec Part D.7. CIRCULAR DEPENDENCY (DB plan §21): team_booking_group_id
is created here as a plain nullable UUID column with NO foreign key.
team_booking_groups does not exist yet (it references bookings.id, so it
must be created after this table) — the FK
    bookings.team_booking_group_id -> team_booking_groups(id)
    DEFERRABLE INITIALLY DEFERRED
is added by migration 0011, once team_booking_groups exists.

The HELD <-> hold_expires_at CHECK constraint is verbatim from spec D.7.
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM as PGEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID

revision: str = "0009_bookings"
down_revision: Union[str, None] = "0008_availability_windows"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

booking_status_enum = PGEnum(
    "REQUESTED",
    "HELD",
    "CONFIRMED",
    "IN_PROGRESS",
    "COMPLETED",
    "REJECTED",
    "EXPIRED",
    "CANCELLED",
    name="booking_status",
    create_type=False,
)


def upgrade() -> None:
    op.create_table(
        "bookings",
        sa.Column("id", PGUUID(as_uuid=True), primary_key=True),
        sa.Column(
            "job_requirement_id",
            PGUUID(as_uuid=True),
            sa.ForeignKey("job_requirements.id"),
            nullable=False,
        ),
        sa.Column(
            "requester_id", PGUUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column("status", booking_status_enum, nullable=False),
        # No FK yet — see module docstring. Added in 0011.
        sa.Column("team_booking_group_id", PGUUID(as_uuid=True), nullable=True),
        sa.Column("hold_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "marked_complete_by_worker_at", sa.DateTime(timezone=True), nullable=True
        ),
        sa.Column(
            "confirmed_complete_by_homeowner_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "cancelled_by", PGUUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True
        ),
        sa.Column("cancellation_reason", sa.Text(), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "(status = 'HELD' AND hold_expires_at IS NOT NULL) "
            "OR (status <> 'HELD' AND hold_expires_at IS NULL)",
            name="ck_bookings_hold_expires_at_matches_status",
        ),
    )
    op.create_index(
        "ix_bookings_job_requirement_id", "bookings", ["job_requirement_id"]
    )
    op.create_index("ix_bookings_requester_id", "bookings", ["requester_id"])
    op.create_index("ix_bookings_status", "bookings", ["status"])
    # Supports the HELD-expiry sweep (`hold_expires_at <= now()` while HELD).
    op.create_index(
        "ix_bookings_hold_expires_at",
        "bookings",
        ["hold_expires_at"],
        postgresql_where=sa.text("status = 'HELD'"),
    )
    # team_booking_group_id has no FK yet, but a booking lookup by it is
    # still a required query path once populated.
    op.create_index(
        "ix_bookings_team_booking_group_id", "bookings", ["team_booking_group_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_bookings_team_booking_group_id", table_name="bookings")
    op.drop_index("ix_bookings_hold_expires_at", table_name="bookings")
    op.drop_index("ix_bookings_status", table_name="bookings")
    op.drop_index("ix_bookings_requester_id", table_name="bookings")
    op.drop_index("ix_bookings_job_requirement_id", table_name="bookings")
    op.drop_table("bookings")
