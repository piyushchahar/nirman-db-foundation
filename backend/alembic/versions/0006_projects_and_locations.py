"""projects and project_locations

Revision ID: 0006_projects_and_locations
Revises: 0005_teams_and_team_members
Create Date: 2026-08-14

spec Part D.6. project_locations matches the spec's verbatim SQL exactly,
including that project_locations.updated_at has no server-side default
in the spec.
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PGUUID

revision: str = "0006_projects_and_locations"
down_revision: Union[str, None] = "0005_teams_and_team_members"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", PGUUID(as_uuid=True), primary_key=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("city", sa.Text(), nullable=True),
        sa.Column("state", sa.Text(), nullable=True),
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
    op.create_index("ix_projects_deleted_at", "projects", ["deleted_at"])

    op.create_table(
        "project_locations",
        sa.Column("id", PGUUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            PGUUID(as_uuid=True),
            sa.ForeignKey("projects.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column("address_line_1", sa.Text(), nullable=False),
        sa.Column("address_line_2", sa.Text(), nullable=True),
        sa.Column("landmark", sa.Text(), nullable=True),
        sa.Column("city", sa.Text(), nullable=False),
        sa.Column("state", sa.Text(), nullable=False),
        sa.Column("postal_code", sa.Text(), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    # No separate index on project_id: it already has unique=True above,
    # which PostgreSQL backs with its own unique index. A second btree
    # index on the identical single column would be an exact duplicate
    # (DB plan §37 "do not create arbitrary indexes").


def downgrade() -> None:
    op.drop_table("project_locations")

    op.drop_index("ix_projects_deleted_at", table_name="projects")
    op.drop_table("projects")
