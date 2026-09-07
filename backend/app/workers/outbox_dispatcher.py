from __future__ import annotations

from datetime import datetime, timezone
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.outbox_event import OutboxEvent


class EventPublisher(Protocol):
    def publish(self, event: OutboxEvent) -> None:
        ...


class OutboxDispatcher:
    def __init__(self, db: Session, publisher: EventPublisher):
        self.db = db
        self.publisher = publisher

    def dispatch_batch(self, limit: int = 50) -> int:
        events = (
            self.db.execute(
                select(OutboxEvent)
                .where(OutboxEvent.processed_at.is_(None))
                .order_by(OutboxEvent.created_at)
                .limit(limit)
                .with_for_update(skip_locked=True)
            )
            .scalars()
            .all()
        )

        dispatched = 0

        for event in events:
            event.attempts += 1
            try:
                self.publisher.publish(event)
                event.processed_at = datetime.now(timezone.utc)
                event.last_error = None
                dispatched += 1
            except Exception as exc:
                event.last_error = str(exc)

        self.db.commit()
        return dispatched
