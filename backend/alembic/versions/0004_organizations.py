"""organizations

Revision ID: 0004_organizations
Revises: 0003_worker_profiles
Create Date: 2026-08-14

Minimal foundation only — see app/models/organization.py docstring for
why business fields (name, etc.) are deferred rather than invented.
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PGUUID

revision: str = "0004_organizations"
down_revision: Union[str, None] = "0003_worker_profiles"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("id", PGUUID(as_uuid=True), primary_key=True),
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
    op.create_index("ix_organizations_deleted_at", "organizations", ["deleted_at"])


def downgrade() -> None:
    op.drop_index("ix_organizations_deleted_at", table_name="organizations")
    op.drop_table("organizations")
