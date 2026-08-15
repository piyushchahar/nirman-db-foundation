"""booking_idempotency

Revision ID: 0015_booking_idempotency
Revises: 0014_shape_rate_triggers
Create Date: 2026-08-14

spec Part D.11, exact. Requester-scoped uniqueness only — DB plan §33
explicitly forbids a globally unique idempotency_key.
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PGUUID

revision: str = "0015_booking_idempotency"
down_revision: Union[str, None] = "0014_shape_rate_triggers"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "booking_idempotency",
        sa.Column("id", PGUUID(as_uuid=True), primary_key=True),
        sa.Column(
            "requester_id", PGUUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column("idempotency_key", sa.Text(), nullable=False),
        sa.Column("request_hash", sa.Text(), nullable=False),
        sa.Column(
            "booking_id", PGUUID(as_uuid=True), sa.ForeignKey("bookings.id"), nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "requester_id", "idempotency_key", name="uq_booking_idempotency_requester_key"
        ),
    )
    op.create_index(
        "ix_booking_idempotency_requester_key",
        "booking_idempotency",
        ["requester_id", "idempotency_key"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_booking_idempotency_requester_key", table_name="booking_idempotency"
    )
    op.drop_table("booking_idempotency")
