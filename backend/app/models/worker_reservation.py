"""
worker_reservations — spec Part D.10, exact.

The authoritative physical reservation representation for worker-overlap
correctness — exists because a GiST exclusion constraint cannot join
through booking_items -> bookings -> job_requirements to obtain the
booking's time range.

`reservation_range` uses TSTZRANGE with [start_time, end_time) semantics.
The GiST exclusion constraint
    EXCLUDE USING gist (worker_profile_id WITH =, reservation_range WITH &&)
is created in the migration (SQLAlchemy's ORM/Core layer has no first-class
EXCLUDE construct, so it is expressed as raw DDL via op.execute, same as
the spec's own `ALTER TABLE ... ADD CONSTRAINT ... EXCLUDE USING gist`).

Active-state strategy: Option A (spec D.10) — a row exists only while its
booking is HELD/REQUESTED/CONFIRMED/IN_PROGRESS; terminal transitions
delete the row in the same transaction as the state transition. That
deletion is BookingStateMachine's responsibility (out of scope for this
task) — this task only creates the table, the CHECK, the UNIQUE
constraint, and the exclusion constraint.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import TSTZRANGE
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class WorkerReservation(Base):
    __tablename__ = "worker_reservations"
    __table_args__ = (
        CheckConstraint(
            "NOT isempty(reservation_range)", name="ck_worker_reservations_range_not_empty"
        ),
        UniqueConstraint(
            "booking_id", "worker_profile_id", name="uq_worker_reservations_booking_worker"
        ),
        # worker_reservations_no_overlap EXCLUDE USING gist(...) is added via
        # raw DDL in the migration; SQLAlchemy Core has no EXCLUDE construct.
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    worker_profile_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("worker_profiles.id"), nullable=False
    )
    booking_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("bookings.id"), nullable=False
    )
    reservation_range: Mapped[str] = mapped_column(TSTZRANGE, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
