"""reviews

Revision ID: 0017_reviews
Revises: 0016_outbox_events
Create Date: 2026-08-14

spec Part D.13, exact. reviewee_id is intentionally not a foreign key —
see app/models/review.py docstring (DEFERRED ARCHITECTURE ITEM:
polymorphic FK target depending on reviewee_type is not specified by
either authoritative document).
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM as PGEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID

revision: str = "0017_reviews"
down_revision: Union[str, None] = "0016_outbox_events"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

reviewee_type_enum = PGEnum(
    "WORKER", "ORGANIZATION", "HOMEOWNER", name="reviewee_type", create_type=False
)


def upgrade() -> None:
    op.create_table(
        "reviews",
        sa.Column("id", PGUUID(as_uuid=True), primary_key=True),
        sa.Column(
            "booking_id", PGUUID(as_uuid=True), sa.ForeignKey("bookings.id"), nullable=False
        ),
        sa.Column(
            "reviewer_id", PGUUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column("reviewee_type", reviewee_type_enum, nullable=False),
        sa.Column("reviewee_id", PGUUID(as_uuid=True), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint("rating >= 1 AND rating <= 5", name="ck_reviews_rating_range"),
        sa.UniqueConstraint(
            "booking_id",
            "reviewer_id",
            "reviewee_type",
            "reviewee_id",
            name="uq_reviews_booking_reviewer_reviewee",
        ),
    )
    op.create_index("ix_reviews_booking_id", "reviews", ["booking_id"])
    op.create_index(
        "ix_reviews_reviewee", "reviews", ["reviewee_type", "reviewee_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_reviews_reviewee", table_name="reviews")
    op.drop_index("ix_reviews_booking_id", table_name="reviews")
    op.drop_table("reviews")
