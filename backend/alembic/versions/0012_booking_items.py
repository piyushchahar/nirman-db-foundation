"""booking_items

Revision ID: 0012_booking_items
Revises: 0011_bookings_team_group_fk
Create Date: 2026-08-14

spec Part D.9, exact, including the WORKER/TEAM resource XOR CHECK
constraint (DB plan §23) and the three indexes named explicitly in the
spec's own DDL block (ix_booking_items_booking_id,
ix_booking_items_worker_profile_id, ix_booking_items_team_id).

Triggers (agreed_rate immutability + deferred shape/status trigger) are
added in migration 0013, after this table exists.
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM as PGEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID

revision: str = "0012_booking_items"
down_revision: Union[str, None] = "0011_bookings_team_group_fk"
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
resource_type_enum = PGEnum(
    "WORKER", "TEAM", name="resource_type", create_type=False
)


def upgrade() -> None:
    op.create_table(
        "booking_items",
        sa.Column("id", PGUUID(as_uuid=True), primary_key=True),
        sa.Column(
            "booking_id", PGUUID(as_uuid=True), sa.ForeignKey("bookings.id"), nullable=False
        ),
        sa.Column("resource_type", resource_type_enum, nullable=False),
        sa.Column(
            "worker_profile_id",
            PGUUID(as_uuid=True),
            sa.ForeignKey("worker_profiles.id"),
            nullable=True,
        ),
        sa.Column(
            "team_id", PGUUID(as_uuid=True), sa.ForeignKey("teams.id"), nullable=True
        ),
        sa.Column(
            "team_booking_group_id",
            PGUUID(as_uuid=True),
            sa.ForeignKey("team_booking_groups.id"),
            nullable=True,
        ),
        sa.Column("status", booking_status_enum, nullable=False),
        sa.Column("agreed_rate", sa.Numeric(10, 2), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "(resource_type = 'WORKER' "
            "  AND worker_profile_id IS NOT NULL "
            "  AND team_id IS NULL "
            "  AND team_booking_group_id IS NULL) "
            "OR "
            "(resource_type = 'TEAM' "
            "  AND team_id IS NOT NULL "
            "  AND worker_profile_id IS NULL "
            "  AND team_booking_group_id IS NOT NULL)",
            name="ck_booking_items_resource_type_xor",
        ),
    )
    op.create_index("ix_booking_items_booking_id", "booking_items", ["booking_id"])
    op.create_index(
        "ix_booking_items_worker_profile_id", "booking_items", ["worker_profile_id"]
    )
    op.create_index("ix_booking_items_team_id", "booking_items", ["team_id"])
    # Supports the deferred shape trigger's group-ownership lookups.
    op.create_index(
        "ix_booking_items_team_booking_group_id",
        "booking_items",
        ["team_booking_group_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_booking_items_team_booking_group_id", table_name="booking_items"
    )
    op.drop_index("ix_booking_items_team_id", table_name="booking_items")
    op.drop_index("ix_booking_items_worker_profile_id", table_name="booking_items")
    op.drop_index("ix_booking_items_booking_id", table_name="booking_items")
    op.drop_table("booking_items")
