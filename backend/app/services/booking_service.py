from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.services.booking_state_machine import BookingStateMachine

class BookingIdempotencyConflictError(ValueError):
    """Raised when an idempotency key is reused with different request data."""


class BookingService:
    """
    Application service for booking workflows.

    Booking creation and state transitions must remain inside PostgreSQL
    transactions. Controllers must not mutate booking state directly.
    """

    def __init__(self, db: Session):
        self.db = db
        self.state_machine = BookingStateMachine(db)

    @staticmethod
    def canonical_request_hash(request_data: dict[str, Any]) -> str:
        """
        Return a deterministic SHA-256 hash of booking-affecting request data.

        Enum values are represented by their underlying values.

        Timezone-aware datetimes are normalized to UTC before hashing.

        JSON key order and insignificant whitespace do not affect the hash.
        Transport metadata such as the Idempotency-Key itself must not be
        included by callers.
        """

        def normalize(value: Any) -> Any:
            if isinstance(value, Enum):
                return normalize(value.value)

            if isinstance(value, datetime):
                if value.tzinfo is None:
                    raise ValueError("Datetime values must be timezone-aware")

                return value.astimezone(timezone.utc).isoformat()

            if isinstance(value, dict):
                return {
                    str(key): normalize(item)
                    for key, item in value.items()
                }

            if isinstance(value, (list, tuple)):
                return [normalize(item) for item in value]

            return value

        canonical = json.dumps(
            normalize(request_data),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )

        return hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest()

    def get_existing_idempotency(
        self,
        requester_id,
        idempotency_key: str,
        request_hash: str,
    ):
        from app.models.booking_idempotency import BookingIdempotency

        record = (
            self.db.query(BookingIdempotency)
            .filter(
                BookingIdempotency.requester_id == requester_id,
                BookingIdempotency.idempotency_key == idempotency_key,
            )
            .one_or_none()
        )

        if record is None:
            return None

        if record.request_hash != request_hash:
            raise BookingIdempotencyConflictError(
                "Idempotency key was already used with different request data"
            )

        return record
    def get_or_create_idempotency(
        self,
        requester_id,
        idempotency_key: str,
        request_hash: str,
        booking_id,
    ):
        from app.models.booking_idempotency import BookingIdempotency

        existing = self.get_existing_idempotency(
            requester_id=requester_id,
            idempotency_key=idempotency_key,
            request_hash=request_hash,
        )

        if existing is not None:
            return existing

        record = BookingIdempotency(
            requester_id=requester_id,
            idempotency_key=idempotency_key,
            request_hash=request_hash,
            booking_id=booking_id,
        )

        try:
            with self.db.begin_nested():
                self.db.add(record)
                self.db.flush()
        except IntegrityError:
            existing = self.get_existing_idempotency(
                requester_id=requester_id,
                idempotency_key=idempotency_key,
                request_hash=request_hash,
            )

            if existing is None:
                raise

            return existing

        return record
