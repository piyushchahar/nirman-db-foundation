"""team_booking_groups

Revision ID: 0010_team_booking_groups
Revises: 0009_bookings
Create Date: 2026-08-14

spec Part D.9a, exact. booking_id is UNIQUE + FK to bookings(id),
DEFERRABLE INITIALLY DEFERRED. This direction of the relationship is not
circular (bookings already exists), so the FK is created directly here.
The reverse FK (bookings.team_booking_group_id -> this table) is added
in migration 0011.
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PGUUID

revision: str = "0010_team_booking_groups"
down_revision: Union[str, None] = "0009_bookings"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "team_booking_groups",
        sa.Column("id", PGUUID(as_uuid=True), primary_key=True),
        sa.Column("booking_id", PGUUID(as_uuid=True), nullable=False, unique=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_foreign_key(
        "fk_team_booking_groups_booking_id",
        "team_booking_groups",
        "bookings",
        ["booking_id"],
        ["id"],
        deferrable=True,
        initially="DEFERRED",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_team_booking_groups_booking_id", "team_booking_groups", type_="foreignkey"
    )
    op.drop_table("team_booking_groups")
