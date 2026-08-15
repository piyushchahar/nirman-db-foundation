"""
job_requirements — spec Part D.5.

`required_skills` is explicitly NOT implemented — DB plan §9/§16 forbid
choosing a representation (TEXT[], JSONB, join table, etc.) without an
authoritative decision. Recorded as a DEFERRED ARCHITECTURE ITEM.

`workers_needed >= 1` and `end_time > start_time` are enforced with
CHECK constraints (DB plan §16 "all required time validity
constraints"; spec D.5 "NOT NULL, CHECK (workers_needed >= 1)").
Booking-related times use TIMESTAMPTZ per DB plan §16.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class JobRequirement(Base):
    __tablename__ = "job_requirements"
    __table_args__ = (
        CheckConstraint("workers_needed >= 1", name="ck_job_requirements_workers_needed_min"),
        CheckConstraint("end_time > start_time", name="ck_job_requirements_valid_time_range"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("projects.id"), nullable=False
    )
    workers_needed: Mapped[int] = mapped_column(Integer, nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
