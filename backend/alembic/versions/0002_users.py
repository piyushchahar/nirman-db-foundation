"""users

Revision ID: 0002_users
Revises: 0001_extensions_and_enums
Create Date: 2026-08-14

spec Part D.1. Only id, authz_version, status, created_at, updated_at
are modeled — see app/models/user.py docstring for why the rest of the
spec's "...existing columns..." placeholder is intentionally not
invented here.
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM as PGEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID

revision: str = "0002_users"
down_revision: Union[str, None] = "0001_extensions_and_enums"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

user_status_enum = PGEnum(
    "ACTIVE", "SUSPENDED", "DISABLED", name="user_status", create_type=False
)


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", PGUUID(as_uuid=True), primary_key=True),
        sa.Column("authz_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", user_status_enum, nullable=False, server_default="ACTIVE"),
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


def downgrade() -> None:
    op.drop_table("users")
