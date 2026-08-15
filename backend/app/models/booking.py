"""
bookings — spec Part D.7, exact.

IMPORTANT — circular dependency handling (DB plan §21):
`bookings.team_booking_group_id` is declared here as a plain nullable
UUID column with NO ForeignKey(...) at the model/migration level that
creates it. `team_booking_groups` does not exist yet when `bookings` is
first created (team_booking_groups.booking_id itself references
bookings). The FK
    bookings.team_booking_group_id -> team_booking_groups(id)
    DEFERRABLE INITIALLY DEFERRED
is added by a dedicated later migration
(0011_bookings_team_group_fk) after both tables exist. This
model still declares the column (nullable, no FK) so SQLAlchemy's
mapped schema matches the table as it exists after all migrations run;
the FK constraint itself is expressed only in the migration, matching
how it is actually created in the database.

The HELD <-> hold_expires_at CHECK constraint is taken verbatim from
spec D.7.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import ENUM as PGEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import BookingStatus

booking_status_enum = PGEnum(
    BookingStatus, name="booking_status", create_type=False, native_enum=True
)


class Booking(Base):
    __tablename__ = "bookings"
    __table_args__ = (
        CheckConstraint(
            "(status = 'HELD' AND hold_expires_at IS NOT NULL) "
            "OR (status <> 'HELD' AND hold_expires_at IS NULL)",
            name="ck_bookings_hold_expires_at_matches_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    job_requirement_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("job_requirements.id"), nullable=False
    )
    requester_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    status: Mapped[BookingStatus] = mapped_column(booking_status_enum, nullable=False)

    # See module docstring: FK added in a later migration.
    team_booking_group_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), nullable=True
    )

    hold_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    marked_complete_by_worker_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    confirmed_complete_by_homeowner_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    cancelled_by: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    cancellation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    # Spec gives no server-side default for bookings.updated_at either;
    # client-side default only, matching the literal DDL in D.7.
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
