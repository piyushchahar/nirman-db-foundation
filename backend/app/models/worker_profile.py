"""
worker_profiles — spec Part D.2.

CRITICAL: no `is_available_now` / `is_available` / `currently_available` /
`is_free` / `current_availability` / `available_now` column exists here,
and none may ever be added to this model. Availability is always derived
at query time from `availability_windows` minus active `worker_reservations`
(spec Part B.6, D.2; DB plan §12, §17).

`hourly_rate` / `daily_rate` use unconstrained PostgreSQL NUMERIC
(no precision/scale). Spec D.2 gives their type as bare `numeric`,
marked "existing" (deferred), with no precision or scale specified
anywhere in either authoritative document — unlike `booking_items.agreed_rate`,
which D.9 explicitly types as `numeric(10,2)`. Inventing a precision here
(e.g. NUMERIC(10,2)) would be an unspecified schema decision.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class WorkerProfile(Base):
    __tablename__ = "worker_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    hourly_rate: Mapped[float | None] = mapped_column(Numeric(), nullable=True)
    daily_rate: Mapped[float | None] = mapped_column(Numeric(), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
