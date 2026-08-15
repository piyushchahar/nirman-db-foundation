"""
availability_windows — spec Part D.4, exact.

No team_id (no team-level availability rows), no is_recurring, no
recurrence_rule — all explicitly removed per spec. No is_available_now
equivalent either (DB plan §12/§17). Availability windows are explicit,
concrete, non-recurring time ranges only.

Index (worker_profile_id, start_time, end_time) is created in the
migration per spec D.4 "Index:" note.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AvailabilityWindow(Base):
    __tablename__ = "availability_windows"
    __table_args__ = (
        CheckConstraint(
            "end_time > start_time", name="ck_availability_windows_valid_time_range"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    worker_profile_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("worker_profiles.id"), nullable=False
    )
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
