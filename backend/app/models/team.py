"""
teams / team_members — spec Part D.3.

`teams` itself is described as "unchanged structurally" with no concrete
column list given in either authoritative document (same situation as
`organizations` — see organization.py docstring). `organization_id` is
included because the API inventory is explicit that teams are created
under an organization (`POST /api/v1/organizations/{id}/teams`) and
`DELETE .../teams/{id}/members/{worker_id}` is scoped to "team belongs to
caller's organization" — this is a structural relationship, not an
invented business field. Other team business fields (name, etc.) are
NOT modeled here; see DEFERRED ARCHITECTURE ITEMS.

`team_members` columns (team_id, worker_profile_id, role, is_active) are
given explicitly in spec Part D.3 and are modeled as specified.
`team_members` reflects CURRENT/FUTURE composition only — it is never
used to reconstruct historical booking participants (that is
`booking_items`'s job; spec Part B.14, D.9; DB plan §14).

DB plan §14 requires that duplicate membership cannot occur where the
architecture requires uniqueness: enforced with
UNIQUE (team_id, worker_profile_id).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class TeamMember(Base):
    __tablename__ = "team_members"
    __table_args__ = (
        UniqueConstraint("team_id", "worker_profile_id", name="uq_team_members_team_worker"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    team_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("teams.id"), nullable=False
    )
    worker_profile_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("worker_profiles.id"), nullable=False
    )
    role: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
