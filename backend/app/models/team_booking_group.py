"""
team_booking_groups — spec Part D.9a, exact.

Small integrity table that prevents unrelated bookings from sharing a
`team_booking_group_id`. `booking_id` is UNIQUE so a group can never be
reused by more than one booking; the FK is DEFERRABLE INITIALLY
DEFERRED per spec so it can be created in the same transaction as its
owning booking if ever needed.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKeyConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TeamBookingGroup(Base):
    __tablename__ = "team_booking_groups"
    __table_args__ = (
        ForeignKeyConstraint(
            ["booking_id"],
            ["bookings.id"],
            name="fk_team_booking_groups_booking_id",
            deferrable=True,
            initially="DEFERRED",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    booking_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), nullable=False, unique=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
