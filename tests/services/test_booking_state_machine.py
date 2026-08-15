from __future__ import annotations

from unittest.mock import Mock

import pytest

from app.models.enums import BookingStatus
from app.services.booking_state_machine import (
    ALLOWED_TRANSITIONS,
    BookingInvalidStateError,
    BookingStateMachine,
)


@pytest.mark.parametrize(
    ("from_status", "to_status"),
    [
        (BookingStatus.REQUESTED, BookingStatus.HELD),
        (BookingStatus.REQUESTED, BookingStatus.REJECTED),
        (BookingStatus.HELD, BookingStatus.CONFIRMED),
        (BookingStatus.HELD, BookingStatus.EXPIRED),
        (BookingStatus.HELD, BookingStatus.REJECTED),
        (BookingStatus.CONFIRMED, BookingStatus.IN_PROGRESS),
        (BookingStatus.CONFIRMED, BookingStatus.CANCELLED),
        (BookingStatus.IN_PROGRESS, BookingStatus.COMPLETED),
        (BookingStatus.IN_PROGRESS, BookingStatus.CANCELLED),
    ],
)
def test_allowed_transitions_are_defined(from_status, to_status):
    assert to_status in ALLOWED_TRANSITIONS[from_status]


@pytest.mark.parametrize(
    ("from_status", "to_status"),
    [
        (BookingStatus.REQUESTED, BookingStatus.CONFIRMED),
        (BookingStatus.REQUESTED, BookingStatus.IN_PROGRESS),
        (BookingStatus.HELD, BookingStatus.IN_PROGRESS),
        (BookingStatus.CONFIRMED, BookingStatus.COMPLETED),
        (BookingStatus.COMPLETED, BookingStatus.IN_PROGRESS),
        (BookingStatus.COMPLETED, BookingStatus.CONFIRMED),
        (BookingStatus.REJECTED, BookingStatus.CONFIRMED),
        (BookingStatus.EXPIRED, BookingStatus.CONFIRMED),
        (BookingStatus.CANCELLED, BookingStatus.CONFIRMED),
    ],
)
def test_forbidden_transitions_are_not_defined(from_status, to_status):
    assert to_status not in ALLOWED_TRANSITIONS[from_status]


def test_terminal_states_have_no_outgoing_transitions():
    assert ALLOWED_TRANSITIONS[BookingStatus.COMPLETED] == frozenset()
    assert ALLOWED_TRANSITIONS[BookingStatus.REJECTED] == frozenset()
    assert ALLOWED_TRANSITIONS[BookingStatus.EXPIRED] == frozenset()
    assert ALLOWED_TRANSITIONS[BookingStatus.CANCELLED] == frozenset()


def test_state_machine_rejects_invalid_transition():
    db = Mock()
    booking = Mock()
    booking.status = BookingStatus.HELD

    state_machine = BookingStateMachine(db)

    with pytest.raises(BookingInvalidStateError):
        state_machine.transition(
            booking,
            BookingStatus.IN_PROGRESS,
        )

    db.flush.assert_not_called()
def test_state_machine_applies_valid_transition():
    db = Mock()
    booking = Mock()
    booking.status = BookingStatus.HELD

    state_machine = BookingStateMachine(db)

    result = state_machine.transition(
        booking,
        BookingStatus.CONFIRMED,
    )

    assert result.from_status == BookingStatus.HELD
    assert result.to_status == BookingStatus.CONFIRMED
    assert booking.status == BookingStatus.CONFIRMED
    db.flush.assert_called_once()
