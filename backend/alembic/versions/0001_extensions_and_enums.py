"""extensions and enums

Revision ID: 0001_extensions_and_enums
Revises:
Create Date: 2026-08-14

Creates the btree_gist extension (required for the worker_reservations
GiST exclusion constraint added in migration 0014) and the PostgreSQL
native enum types used throughout the schema:

- user_status      (spec D.1)
- booking_status    (spec D.7 / D.8, full whitelist)
- resource_type     (spec D.9)
- reviewee_type     (spec D.13)

Enums are created here, ahead of any table, and referenced from later
migrations with create_type=False so each enum type is created exactly
once.
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM as PGEnum

revision: str = "0001_extensions_and_enums"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")

    PGEnum("ACTIVE", "SUSPENDED", "DISABLED", name="user_status").create(
        op.get_bind(), checkfirst=True
    )
    PGEnum(
        "REQUESTED",
        "HELD",
        "CONFIRMED",
        "IN_PROGRESS",
        "COMPLETED",
        "REJECTED",
        "EXPIRED",
        "CANCELLED",
        name="booking_status",
    ).create(op.get_bind(), checkfirst=True)
    PGEnum("WORKER", "TEAM", name="resource_type").create(op.get_bind(), checkfirst=True)
    PGEnum("WORKER", "ORGANIZATION", "HOMEOWNER", name="reviewee_type").create(
        op.get_bind(), checkfirst=True
    )


def downgrade() -> None:
    PGEnum(name="reviewee_type").drop(op.get_bind(), checkfirst=True)
    PGEnum(name="resource_type").drop(op.get_bind(), checkfirst=True)
    PGEnum(name="booking_status").drop(op.get_bind(), checkfirst=True)
    PGEnum(name="user_status").drop(op.get_bind(), checkfirst=True)

    # btree_gist is left in place on downgrade: dropping an extension that
    # another database object might depend on is unsafe to do unconditionally,
    # and PostgreSQL will itself raise a clear dependency error via
    # `DROP EXTENSION` if something still depends on it. We drop it here only
    # if nothing depends on it, matching "downgrade base -> truly empty db".
    op.execute("DROP EXTENSION IF EXISTS btree_gist")
