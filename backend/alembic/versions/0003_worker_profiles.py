"""worker_profiles

Revision ID: 0003_worker_profiles
Revises: 0002_users
Create Date: 2026-08-14

spec Part D.2. No is_available_now / is_available / currently_available /
is_free / current_availability / available_now column — see
app/models/worker_profile.py docstring.

hourly_rate / daily_rate use unconstrained NUMERIC (no precision/scale):
spec D.2 does not define precision/scale for these columns, so none is
invented here. This differs from booking_items.agreed_rate (0012), which
spec D.9 explicitly types as numeric(10,2).
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PGUUID

revision: str = "0003_worker_profiles"
down_revision: Union[str, None] = "0002_users"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "worker_profiles",
        sa.Column("id", PGUUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            PGUUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("hourly_rate", sa.Numeric(), nullable=True),
        sa.Column("daily_rate", sa.Numeric(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
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
    )
    op.create_index("ix_worker_profiles_user_id", "worker_profiles", ["user_id"])
    # Supports "public discovery... queries mandatory deleted_at IS NULL" (D.14).
    op.create_index(
        "ix_worker_profiles_deleted_at",
        "worker_profiles",
        ["deleted_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_worker_profiles_deleted_at", table_name="worker_profiles")
    op.drop_index("ix_worker_profiles_user_id", table_name="worker_profiles")
    op.drop_table("worker_profiles")
