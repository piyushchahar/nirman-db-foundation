"""teams and team_members

Revision ID: 0005_teams_and_team_members
Revises: 0004_organizations
Create Date: 2026-08-14

spec Part D.3. team_members duplicate-membership prevention via
UNIQUE(team_id, worker_profile_id) per DB plan §14.
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PGUUID

revision: str = "0005_teams_and_team_members"
down_revision: Union[str, None] = "0004_organizations"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "teams",
        sa.Column("id", PGUUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            PGUUID(as_uuid=True),
            sa.ForeignKey("organizations.id"),
            nullable=False,
        ),
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
    op.create_index("ix_teams_organization_id", "teams", ["organization_id"])
    op.create_index("ix_teams_deleted_at", "teams", ["deleted_at"])

    op.create_table(
        "team_members",
        sa.Column("id", PGUUID(as_uuid=True), primary_key=True),
        sa.Column(
            "team_id", PGUUID(as_uuid=True), sa.ForeignKey("teams.id"), nullable=False
        ),
        sa.Column(
            "worker_profile_id",
            PGUUID(as_uuid=True),
            sa.ForeignKey("worker_profiles.id"),
            nullable=False,
        ),
        sa.Column("role", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "team_id", "worker_profile_id", name="uq_team_members_team_worker"
        ),
    )
    # Team-membership lookups (DB plan §37 "team membership"). No separate
    # index on team_id alone: uq_team_members_team_worker (team_id,
    # worker_profile_id) already covers team_id-only lookups via its
    # leftmost-prefix; a standalone index would be redundant (DB plan §37
    # "do not create arbitrary indexes"). worker_profile_id is NOT covered
    # by that composite index's prefix, so it still needs its own index.
    op.create_index(
        "ix_team_members_worker_profile_id", "team_members", ["worker_profile_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_team_members_worker_profile_id", table_name="team_members")
    op.drop_table("team_members")

    op.drop_index("ix_teams_deleted_at", table_name="teams")
    op.drop_index("ix_teams_organization_id", table_name="teams")
    op.drop_table("teams")
