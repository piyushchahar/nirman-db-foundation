"""
reviews — spec Part D.13, exact.

`reviewee_id` is intentionally NOT a foreign key at the database level:
its FK target depends on `reviewee_type` (WORKER -> worker_profiles,
ORGANIZATION -> organizations, HOMEOWNER -> users) which PostgreSQL FKs
cannot express polymorphically without a much heavier schema (e.g.
separate nullable FK columns per type) that neither authoritative
document specifies. The spec states reviewee_id is "validated against
booking resource" — that is explicitly application-layer validation
(ReviewService, out of scope for this task), not a DB-level FK. This is
recorded as a DEFERRED ARCHITECTURE ITEM rather than inventing a
polymorphic-FK schema.

UNIQUE (booking_id, reviewer_id, reviewee_type, reviewee_id) prevents
duplicate reviewer/reviewee/booking combinations, per spec.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import ENUM as PGEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import RevieweeType

reviewee_type_enum = PGEnum(
    RevieweeType, name="reviewee_type", create_type=False, native_enum=True
)


class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5", name="ck_reviews_rating_range"),
        UniqueConstraint(
            "booking_id",
            "reviewer_id",
            "reviewee_type",
            "reviewee_id",
            name="uq_reviews_booking_reviewer_reviewee",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    booking_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("bookings.id"), nullable=False
    )
    reviewer_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    reviewee_type: Mapped[RevieweeType] = mapped_column(reviewee_type_enum, nullable=False)
    # Intentionally not a ForeignKey — see module docstring.
    reviewee_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
