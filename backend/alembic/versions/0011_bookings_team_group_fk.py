"""add bookings.team_booking_group_id FK

Revision ID: 0011_bookings_team_group_fk
Revises: 0010_team_booking_groups
Create Date: 2026-08-14

Resolves the circular dependency called out in DB plan §21: now that
team_booking_groups exists (migration 0010), the FK
    bookings.team_booking_group_id -> team_booking_groups(id)
    DEFERRABLE INITIALLY DEFERRED
from spec D.7's CREATE TABLE bookings statement can finally be added.

NOTE ON REVISION ID LENGTH: originally named
"0011_add_bookings_team_booking_group_fk" (39 characters), which exceeds
the 32-character width of Alembic's own internal `alembic_version.version_num`
bookkeeping column. That table is Alembic tooling infrastructure, not part
of the Nirman domain schema, so shortening this identifier does not touch
any table/column/constraint defined by the spec or DB plan — only
Alembic's own revision-tracking id string.
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0011_bookings_team_group_fk"
down_revision: Union[str, None] = "0010_team_booking_groups"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_foreign_key(
        "fk_bookings_team_booking_group_id",
        "bookings",
        "team_booking_groups",
        ["team_booking_group_id"],
        ["id"],
        deferrable=True,
        initially="DEFERRED",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_bookings_team_booking_group_id", "bookings", type_="foreignkey"
    )
