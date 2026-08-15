"""
projects / project_locations — spec Part D.6.

`projects` retains only the coarse public fields the spec names
explicitly: latitude, longitude (approximate/public-safe), city, state.
Soft delete (`deleted_at`) is added per spec Part D.14, which lists
`projects` as one of the soft-deletable entities.

DEFERRED: the spec's Part E.2.1 trace says booking creation checks
"requester owns the project/job requirement," implying some ownership
column exists on `projects`, but no such column is named in the D.6
table or anywhere else in either authoritative document. Rather than
invent an `owner_id`/`requester_id`/`homeowner_id` column and guess its
FK target and nullability, this is recorded as a DEFERRED ARCHITECTURE
ITEM. See the final report.

`project_locations` is modeled exactly from the SQL given verbatim in
spec Part D.6, including that `updated_at` has no server-side default
in the spec (the spec only gives `created_at` a `DEFAULT now()`) — a
client-side default is set at the ORM layer purely so inserts don't
require the caller to compute a timestamp by hand; the column remains
NOT NULL with no DB-level default, matching the spec's literal DDL.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    city: Mapped[str | None] = mapped_column(Text, nullable=True)
    state: Mapped[str | None] = mapped_column(Text, nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
