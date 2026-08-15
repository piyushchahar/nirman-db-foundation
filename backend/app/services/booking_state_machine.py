from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.booking import Booking
from app.models.enums import BookingStatus


class BookingInvalidStateError(Exception):
    """Raised when a booking attempts an illegal state transition."""


@dataclass(frozen=True)
class BookingTransition:
    from_status: BookingStatus | None
    to_status: BookingStatus


ALLOWED_TRANSITIONS: dict[BookingStatus | None, frozenset[BookingStatus]] = {
    BookingStatus.REQUESTED: frozenset(
        {
            BookingStatus.HELD,
            BookingStatus.REJECTED,
        }
    ),
    BookingStatus.HELD: frozenset(
        {
            BookingStatus.CONFIRMED,
            BookingStatus.EXPIRED,
            BookingStatus.REJECTED,
        }
    ),
    BookingStatus.CONFIRMED: frozenset(
        {
            BookingStatus.IN_PROGRESS,
            BookingStatus.CANCELLED,
        }
    ),
    BookingStatus.IN_PROGRESS: frozenset(
        {
            BookingStatus.COMPLETED,
            BookingStatus.CANCELLED,
        }
    ),
    BookingStatus.COMPLETED: frozenset(),
    BookingStatus.REJECTED: frozenset(),
    BookingStatus.EXPIRED: frozenset(),
    BookingStatus.CANCELLED: frozenset(),
}


class BookingStateMachine:
    """
    Authoritative application-level booking transition validator.

    This class only owns transition legality and the booking status mutation.
    Reservation release/creation, booking-item synchronization, audit logging,
    and outbox writes will be added by the booking service as those application
    components are implemented.
    """

    def __init__(self, db: Session):
        self.db = db

    def transition(
        self,
        booking: Booking,
        to_status: BookingStatus,
    ) -> BookingTransition:
        current_status = booking.status

        allowed = ALLOWED_TRANSITIONS.get(current_status, frozenset())

        if to_status not in allowed:
            raise BookingInvalidStateError(
                f"Invalid booking state transition: "
                f"{current_status.value} -> {to_status.value}"
            )

        booking.status = to_status
        self.db.flush()

        return BookingTransition(
            from_status=current_status,
            to_status=to_status,
        )
