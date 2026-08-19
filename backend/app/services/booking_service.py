from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.services.booking_state_machine import BookingStateMachine
from app.models.enums import BookingStatus

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
    def create_booking(
        self,
        job_requirement_id,
        requester_id,
    ):
        from app.models.booking import Booking
        from app.models.enums import BookingStatus

        booking = Booking(
            job_requirement_id=job_requirement_id,
            requester_id=requester_id,
            status=BookingStatus.REQUESTED,
            hold_expires_at=None,
        )

        self.db.add(booking)
        self.db.flush()

        return booking
    def create_booking_idempotent(
        self,
        *,
        requester_id,
        job_requirement_id,
        idempotency_key: str,
        request_data: dict[str, Any],
    ):
        """
        Create a booking and its idempotency record as one transaction unit.

        The caller owns the outer transaction. This method does not commit.
        Repeated requests with the same requester/key and identical request
        data return the existing idempotency record's booking.
        Reuse of the key with different request data raises
        BookingIdempotencyConflictError.
        """
        request_hash = self.canonical_request_hash(request_data)

        existing = self.get_existing_idempotency(
            requester_id=requester_id,
            idempotency_key=idempotency_key,
            request_hash=request_hash,
        )

        if existing is not None:
            return self.db.get(
                __import__(
                    "app.models.booking",
                    fromlist=["Booking"],
                ).Booking,
                existing.booking_id,
            )

        booking = self.create_booking(
            job_requirement_id=job_requirement_id,
            requester_id=requester_id,
        )

        self.get_or_create_idempotency(
            requester_id=requester_id,
            idempotency_key=idempotency_key,
            request_hash=request_hash,
            booking_id=booking.id,
        )

        return booking
    def hold_booking(
        self,
        booking,
        hold_expires_at: datetime,
    ):
        """
        Move a REQUESTED booking to HELD with an explicit hold expiry.

        The caller owns the surrounding transaction. This method does not
        commit.
        """
        if hold_expires_at.tzinfo is None:
            raise ValueError("hold_expires_at must be timezone-aware")

        previous_expiry = booking.hold_expires_at
        booking.hold_expires_at = hold_expires_at

        try:
            self.state_machine.transition(
                booking,
                BookingStatus.HELD,
            )
        except Exception:
            booking.hold_expires_at = previous_expiry
            raise

        return booking
    def confirm_booking(self, booking):
        """
        Move a HELD booking to CONFIRMED.

        Confirmation clears the temporary hold expiry because the booking
        is no longer in the HELD state.

        The caller owns the surrounding transaction. This method does not
        commit.
        """
        previous_expiry = booking.hold_expires_at
        booking.hold_expires_at = None

        try:
            self.state_machine.transition(
                booking,
                BookingStatus.CONFIRMED,
            )
        except Exception:
            booking.hold_expires_at = previous_expiry
            raise

        return booking
    def expire_booking(self, booking):
        """
        Move a HELD booking to EXPIRED.

        The hold expiry is cleared because the booking is no longer HELD.
        The caller owns the surrounding transaction. This method does not
        commit.
        """
        previous_expiry = booking.hold_expires_at
        booking.hold_expires_at = None

        try:
            self.state_machine.transition(
                booking,
                BookingStatus.EXPIRED,
            )
        except Exception:
            booking.hold_expires_at = previous_expiry
            raise

        return booking
