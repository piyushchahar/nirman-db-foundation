from __future__ import annotations

import uuid
from unittest.mock import Mock

import sqlalchemy as sa
from sqlalchemy.orm import Session

from app.models.outbox_event import OutboxEvent
from app.workers.outbox_dispatcher import OutboxDispatcher


def test_dispatcher_publishes_and_marks_processed(db_conn):
    event_id = uuid.uuid4()
    publisher = Mock()

    db_conn.execute(
        sa.text(
            "INSERT INTO outbox_events "
            "(id, event_type, aggregate_type, aggregate_id, payload) "
            "VALUES (:id, 'BookingCompleted', 'Booking', :aggregate_id, "
            "'{\"booking_id\": \"test\"}'::jsonb)"
        ),
        {"id": event_id, "aggregate_id": uuid.uuid4()},
    )

    try:
        with Session(bind=db_conn, future=True) as db:
            dispatcher = OutboxDispatcher(db, publisher)
            assert dispatcher.dispatch_batch() == 1

        row = db_conn.execute(
            sa.text(
                "SELECT processed_at, attempts, last_error "
                "FROM outbox_events WHERE id = :id"
            ),
            {"id": event_id},
        ).one()

        publisher.publish.assert_called_once()
        assert row.processed_at is not None
        assert row.attempts == 1
        assert row.last_error is None
    finally:
        db_conn.execute(
            sa.text("DELETE FROM outbox_events WHERE id = :id"),
            {"id": event_id},
        )


def test_dispatcher_keeps_failed_event_retryable(db_conn):
    event_id = uuid.uuid4()
    publisher = Mock()
    publisher.publish.side_effect = RuntimeError("temporary failure")

    db_conn.execute(
        sa.text(
            "INSERT INTO outbox_events "
            "(id, event_type, aggregate_type, aggregate_id, payload) "
            "VALUES (:id, 'BookingCompleted', 'Booking', :aggregate_id, "
            "'{\"booking_id\": \"test\"}'::jsonb)"
        ),
        {"id": event_id, "aggregate_id": uuid.uuid4()},
    )

    try:
        with Session(bind=db_conn, future=True) as db:
            dispatcher = OutboxDispatcher(db, publisher)
            assert dispatcher.dispatch_batch() == 0

        row = db_conn.execute(
            sa.text(
                "SELECT processed_at, attempts, last_error "
                "FROM outbox_events WHERE id = :id"
            ),
            {"id": event_id},
        ).one()

        assert row.processed_at is None
        assert row.attempts == 1
        assert row.last_error == "temporary failure"
    finally:
        db_conn.execute(
            sa.text("DELETE FROM outbox_events WHERE id = :id"),
            {"id": event_id},
        )
