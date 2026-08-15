"""outbox_events

Revision ID: 0016_outbox_events
Revises: 0015_booking_idempotency
Create Date: 2026-08-14

spec Part D.12, exact. Persistence layer only — no dispatcher, no
Celery, no publishing (DB plan §34/§46). Indexes match spec's own DDL
(ix_outbox_pending, ix_outbox_aggregate) to support a future
`SELECT ... FOR UPDATE SKIP LOCKED` dispatcher.
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID

revision: str = "0016_outbox_events"
down_revision: Union[str, None] = "0015_booking_idempotency"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "outbox_events",
        sa.Column("id", PGUUID(as_uuid=True), primary_key=True),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("aggregate_type", sa.Text(), nullable=False),
        sa.Column("aggregate_id", PGUUID(as_uuid=True), nullable=False),
        sa.Column("payload", JSONB(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_error", sa.Text(), nullable=True),
    )
    op.create_index(
        "ix_outbox_pending", "outbox_events", ["processed_at", "created_at"]
    )
    op.create_index(
        "ix_outbox_aggregate", "outbox_events", ["aggregate_type", "aggregate_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_outbox_aggregate", table_name="outbox_events")
    op.drop_index("ix_outbox_pending", table_name="outbox_events")
    op.drop_table("outbox_events")
