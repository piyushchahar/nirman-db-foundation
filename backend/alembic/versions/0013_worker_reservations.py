"""worker_reservations

Revision ID: 0013_worker_reservations
Revises: 0012_booking_items
Create Date: 2026-08-14

spec Part D.10, exact. CRITICAL requirement (DB plan §30): the GiST
exclusion constraint
    EXCLUDE USING gist (worker_profile_id WITH =, reservation_range WITH &&)
is the sole, final correctness authority preventing overlapping worker
reservations — no Python/application-level substitute is used anywhere
in this task (DB plan §44, §29-32).

btree_gist (migration 0001) is required for this constraint to support
equality (=) on a UUID column inside a GiST exclusion constraint.
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import TSTZRANGE
from sqlalchemy.dialects.postgresql import UUID as PGUUID

revision: str = "0013_worker_reservations"
down_revision: Union[str, None] = "0012_booking_items"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "worker_reservations",
        sa.Column("id", PGUUID(as_uuid=True), primary_key=True),
        sa.Column(
            "worker_profile_id",
            PGUUID(as_uuid=True),
            sa.ForeignKey("worker_profiles.id"),
            nullable=False,
        ),
        sa.Column(
            "booking_id", PGUUID(as_uuid=True), sa.ForeignKey("bookings.id"), nullable=False
        ),
        sa.Column("reservation_range", TSTZRANGE(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "NOT isempty(reservation_range)",
            name="ck_worker_reservations_range_not_empty",
        ),
        sa.UniqueConstraint(
            "booking_id", "worker_profile_id", name="uq_worker_reservations_booking_worker"
        ),
    )
    # worker_profile_id needs its own index (not a leftmost prefix of the
    # composite unique constraint below). No separate index on booking_id
    # alone: uq_worker_reservations_booking_worker (booking_id,
    # worker_profile_id) already covers booking_id-only lookups via its
    # leftmost prefix, so a standalone index would be redundant (DB plan
    # §37 "do not create arbitrary indexes").
    op.create_index(
        "ix_worker_reservations_worker_profile_id",
        "worker_reservations",
        ["worker_profile_id"],
    )

    # SQLAlchemy Core has no first-class EXCLUDE construct; expressed as raw
    # DDL, identical in effect to the spec's own
    # `ALTER TABLE ... ADD CONSTRAINT ... EXCLUDE USING gist (...)`.
    op.execute(
        """
        ALTER TABLE worker_reservations
        ADD CONSTRAINT worker_reservations_no_overlap
        EXCLUDE USING gist (
            worker_profile_id WITH =,
            reservation_range WITH &&
        )
        """
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE worker_reservations DROP CONSTRAINT worker_reservations_no_overlap"
    )
    op.drop_index(
        "ix_worker_reservations_worker_profile_id", table_name="worker_reservations"
    )
    op.drop_table("worker_reservations")
