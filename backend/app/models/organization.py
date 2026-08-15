"""
organizations — DEFERRED ARCHITECTURE ITEM.

The spec explicitly states organizations is an "existing unaffected
table... assumed unchanged and referenced but not re-specified"
(spec Part D, intro to Part D). No concrete column list (name, owner,
verification status, etc.) is given anywhere in either authoritative
document; the API inventory only says "existing organization creation
fields" without defining them.

Per DB plan §13 ("Do not invent unrelated organization business
fields") this model implements only what is unambiguously required by
other, fully-specified parts of the schema:

- id: referenced by teams.organization_id (organizations own teams,
  per the API inventory: POST /api/v1/organizations/{id}/teams) and by
  reviews.reviewee_id when reviewee_type = ORGANIZATION.
- deleted_at: organizations are listed as a soft-deletable entity in
  spec Part D.14.
- created_at / updated_at: standard foundation timestamps, consistent
  with every other foundation table in this schema.

All other organization business fields (name, description, verification
status, owner/contact info, etc.) are intentionally NOT modeled here.
See DEFERRED ARCHITECTURE ITEMS in the final report.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
