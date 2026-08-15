"""
booking_items — spec Part D.9, exact.

Immutable historical resource snapshot. Not the reservation table — no
start_time/end_time/reservation_range/exclusion constraint here (that is
worker_reservations, D.10).

The WORKER/TEAM resource XOR is enforced with the exact CHECK constraint
given in the spec (DB plan §23):
  resource_type = WORKER -> worker_profile_id NOT NULL, team_id NULL,
                             team_booking_group_id NULL
  resource_type = TEAM   -> team_id NOT NULL, worker_profile_id NULL,
                             team_booking_group_id NOT NULL

Two deferred constraint triggers are attached to this table at the
migration level (not modeled here, since SQLAlchemy's ORM layer does not
express triggers): `booking_items_agreed_rate_immutable` (spec D.9,
verbatim) and the booking-shape/status-consistency deferred trigger
(spec D.9b). See migrations 0013 and the trigger SQL files.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, func
from sqlalchemy.dialects.postgresql import ENUM as PGEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.booking import booking_status_enum
from app.models.enums import ResourceType

resource_type_enum = PGEnum(
    ResourceType, name="resource_type", create_type=False, native_enum=True
)


class BookingItem(Base):
    __tablename__ = "booking_items"
    __table_args__ = (
        CheckConstraint(
            "(resource_type = 'WORKER' "
            "  AND worker_profile_id IS NOT NULL "
            "  AND team_id IS NULL "
            "  AND team_booking_group_id IS NULL) "
            "OR "
            "(resource_type = 'TEAM' "
            "  AND team_id IS NOT NULL "
            "  AND worker_profile_id IS NULL "
            "  AND team_booking_group_id IS NOT NULL)",
            name="ck_booking_items_resource_type_xor",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    booking_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("bookings.id"), nullable=False
    )
    resource_type: Mapped[ResourceType] = mapped_column(resource_type_enum, nullable=False)
    worker_profile_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("worker_profiles.id"), nullable=True
    )
    team_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("teams.id"), nullable=True
    )
    team_booking_group_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("team_booking_groups.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(booking_status_enum, nullable=False)
    agreed_rate: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
