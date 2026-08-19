from __future__ import annotations


from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, Mock
from uuid import uuid4

import pytest

from app.models.enums import BookingStatus
from app.services.booking_service import (
    BookingIdempotencyConflictError,
    BookingService,
)

def test_canonical_hash_is_stable_when_dict_key_order_changes():
    first = {
        "job_requirement_id": "job-1",
        "resource_type": "WORKER",
        "resource_id": "worker-1",
    }

    second = {
        "resource_id": "worker-1",
        "job_requirement_id": "job-1",
        "resource_type": "WORKER",
    }

    assert BookingService.canonical_request_hash(first) == (
        BookingService.canonical_request_hash(second)
    )


def test_canonical_hash_changes_when_booking_data_changes():
    first = {
        "job_requirement_id": "job-1",
        "resource_type": "WORKER",
        "resource_id": "worker-1",
    }

    second = {
        "job_requirement_id": "job-1",
        "resource_type": "WORKER",
        "resource_id": "worker-2",
    }

    assert BookingService.canonical_request_hash(first) != (
        BookingService.canonical_request_hash(second)
    )


def test_canonical_hash_ignores_insignificant_json_whitespace():
    first = {
        "resource_type": "WORKER",
        "resource_id": "worker-1",
    }

    second = {
        "resource_type": "WORKER",
        "resource_id": "worker-1",
    }

    assert BookingService.canonical_request_hash(first) == (
        BookingService.canonical_request_hash(second)
    )


def test_canonical_hash_normalizes_enums():
    enum_data = {
        "status": BookingStatus.HELD,
    }

    string_data = {
        "status": "HELD",
    }

    assert BookingService.canonical_request_hash(enum_data) == (
        BookingService.canonical_request_hash(string_data)
    )


def test_canonical_hash_normalizes_equivalent_timestamps_to_utc():
    utc_time = datetime(
        2026,
        9,
        2,
        13,
        0,
        tzinfo=timezone.utc,
    )

    eastern_time = datetime(
        2026,
        9,
        2,
        8,
        0,
        tzinfo=timezone(timedelta(hours=-5)),
    )

    first = {"start_time": utc_time}
    second = {"start_time": eastern_time}

    assert BookingService.canonical_request_hash(first) == (
        BookingService.canonical_request_hash(second)
    )


def test_get_existing_idempotency_returns_none_when_key_is_new():
    db = Mock()
    db.query.return_value.filter.return_value.one_or_none.return_value = None

    service = BookingService(db)

    result = service.get_existing_idempotency(
        requester_id=uuid4(),
        idempotency_key="new-key",
        request_hash="hash-a",
    )

    assert result is None

def test_get_existing_idempotency_returns_matching_record():
    from unittest.mock import Mock

    requester_id = uuid4()

    record = Mock()
    record.request_hash = "hash-a"

    db = Mock()
    db.query.return_value.filter.return_value.one_or_none.return_value = record

    service = BookingService(db)

    result = service.get_existing_idempotency(
        requester_id=requester_id,
        idempotency_key="existing-key",
        request_hash="hash-a",
    )

    assert result is record


def test_get_existing_idempotency_rejects_different_request_hash():
    from unittest.mock import Mock

    record = Mock()
    record.request_hash = "hash-a"

    db = Mock()
    db.query.return_value.filter.return_value.one_or_none.return_value = record

    service = BookingService(db)

    with pytest.raises(ValueError, match="different request data"):
        service.get_existing_idempotency(
            requester_id=uuid4(),
            idempotency_key="existing-key",
            request_hash="hash-b",
        )
def test_get_or_create_idempotency_creates_new_record():
    from app.models.booking_idempotency import BookingIdempotency

    db = MagicMock()
    db.query.return_value.filter.return_value.one_or_none.return_value = None

    service = BookingService(db)

    requester_id = uuid4()
    booking_id = uuid4()

    result = service.get_or_create_idempotency(
        requester_id=requester_id,
        idempotency_key="new-key",
        request_hash="hash-a",
        booking_id=booking_id,
    )

    assert isinstance(result, BookingIdempotency)
    assert result.requester_id == requester_id
    assert result.idempotency_key == "new-key"
    assert result.request_hash == "hash-a"
    assert result.booking_id == booking_id

    db.add.assert_called_once_with(result)
    db.flush.assert_called_once()
def test_create_booking_starts_in_requested_state():
    from app.models.booking import Booking

    db = MagicMock()
    service = BookingService(db)

    job_requirement_id = uuid4()
    requester_id = uuid4()

    result = service.create_booking(
        job_requirement_id=job_requirement_id,
        requester_id=requester_id,
    )

    assert isinstance(result, Booking)
    assert result.job_requirement_id == job_requirement_id
    assert result.requester_id == requester_id
    assert result.status == BookingStatus.REQUESTED
    assert result.hold_expires_at is None

    db.add.assert_called_once_with(result)
    db.flush.assert_called_once()


def test_create_booking_does_not_commit_transaction():
    db = MagicMock()
    service = BookingService(db)

    service.create_booking(
        job_requirement_id=uuid4(),
        requester_id=uuid4(),
    )

    db.commit.assert_not_called()
def test_create_booking_idempotent_creates_booking_for_new_key():
    db = MagicMock()
    db.query.return_value.filter.return_value.one_or_none.return_value = None

    service = BookingService(db)

    requester_id = uuid4()
    job_requirement_id = uuid4()

    result = service.create_booking_idempotent(
        requester_id=requester_id,
        job_requirement_id=job_requirement_id,
        idempotency_key="new-key",
        request_data={
            "job_requirement_id": str(job_requirement_id),
            "resource_type": "WORKER",
        },
    )

    assert result.requester_id == requester_id
    assert result.job_requirement_id == job_requirement_id
    assert result.status == BookingStatus.REQUESTED

    db.add.assert_any_call(result)
    db.flush.assert_called()


def test_create_booking_idempotent_returns_existing_booking_for_same_request():
    requester_id = uuid4()
    job_requirement_id = uuid4()
    booking_id = uuid4()

    existing_idempotency = Mock()
    existing_idempotency.request_hash = BookingService.canonical_request_hash(
        {
            "job_requirement_id": str(job_requirement_id),
            "resource_type": "WORKER",
        }
    )
    existing_idempotency.booking_id = booking_id

    existing_booking = Mock()
    existing_booking.id = booking_id

    db = MagicMock()
    db.query.return_value.filter.return_value.one_or_none.return_value = (
        existing_idempotency
    )
    db.get.return_value = existing_booking

    service = BookingService(db)

    result = service.create_booking_idempotent(
        requester_id=requester_id,
        job_requirement_id=job_requirement_id,
        idempotency_key="existing-key",
        request_data={
            "job_requirement_id": str(job_requirement_id),
            "resource_type": "WORKER",
        },
    )

    assert result is existing_booking
    db.get.assert_called_once()
    db.add.assert_not_called()


def test_create_booking_idempotent_rejects_same_key_with_different_request():
    requester_id = uuid4()
    job_requirement_id = uuid4()

    existing_idempotency = Mock()
    existing_idempotency.request_hash = "different-hash"

    db = MagicMock()
    db.query.return_value.filter.return_value.one_or_none.return_value = (
        existing_idempotency
    )

    service = BookingService(db)

    with pytest.raises(
        BookingIdempotencyConflictError,
        match="different request data",
    ):
        service.create_booking_idempotent(
            requester_id=requester_id,
            job_requirement_id=job_requirement_id,
            idempotency_key="existing-key",
            request_data={
                "job_requirement_id": str(job_requirement_id),
                "resource_type": "WORKER",
            },
        )

    db.add.assert_not_called()
def test_hold_booking_sets_expiry_and_transitions_to_held():
    db = MagicMock()
    service = BookingService(db)

    booking = Mock()
    booking.status = BookingStatus.REQUESTED
    booking.hold_expires_at = None

    expires_at = datetime(
        2026,
        9,
        2,
        13,
        0,
        tzinfo=timezone.utc,
    )

    service.hold_booking(
        booking,
        expires_at,
    )

    assert booking.hold_expires_at == expires_at
    assert booking.status == BookingStatus.HELD
    db.flush.assert_called_once()


def test_hold_booking_rejects_naive_expiry():
    db = MagicMock()
    service = BookingService(db)

    booking = Mock()
    booking.status = BookingStatus.REQUESTED
    booking.hold_expires_at = None

    naive_expiry = datetime(2026, 9, 2, 13, 0)

    with pytest.raises(
        ValueError,
        match="timezone-aware",
    ):
        service.hold_booking(
            booking,
            naive_expiry,
        )

    db.flush.assert_not_called()


def test_hold_booking_restores_expiry_when_transition_fails():
    db = MagicMock()
    service = BookingService(db)

    booking = Mock()
    booking.status = BookingStatus.HELD
    booking.hold_expires_at = None

    expires_at = datetime(
        2026,
        9,
        2,
        13,
        0,
        tzinfo=timezone.utc,
    )

    with pytest.raises(Exception):
        service.hold_booking(
            booking,
            expires_at,
        )

    assert booking.hold_expires_at is None
def test_confirm_booking_moves_held_to_confirmed_and_clears_hold_expiry():
    db = Mock()
    service = BookingService(db)

    booking = Mock()
    booking.status = BookingStatus.HELD
    booking.hold_expires_at = datetime(
        2026,
        9,
        3,
        12,
        0,
        tzinfo=timezone.utc,
    )

    result = service.confirm_booking(booking)

    assert result is booking
    assert booking.status == BookingStatus.CONFIRMED
    assert booking.hold_expires_at is None


def test_confirm_booking_rejects_non_held_booking():
    db = Mock()
    service = BookingService(db)

    booking = Mock()
    booking.status = BookingStatus.REQUESTED
    booking.hold_expires_at = None

    with pytest.raises(Exception, match="Invalid booking state transition"):
        service.confirm_booking(booking)

    assert booking.status == BookingStatus.REQUESTED
    assert booking.hold_expires_at is None


def test_confirm_booking_restores_hold_expiry_when_transition_fails():
    db = Mock()
    service = BookingService(db)

    booking = Mock()
    booking.status = BookingStatus.REQUESTED

    original_expiry = datetime(
        2026,
        9,
        3,
        12,
        0,
        tzinfo=timezone.utc,
    )
    booking.hold_expires_at = original_expiry

    with pytest.raises(Exception, match="Invalid booking state transition"):
        service.confirm_booking(booking)

    assert booking.status == BookingStatus.REQUESTED
    assert booking.hold_expires_at == original_expiry
def test_expire_booking_moves_held_to_expired_and_clears_hold_expiry():
    db = Mock()
    service = BookingService(db)

    booking = Mock()
    booking.status = BookingStatus.HELD
    booking.hold_expires_at = datetime(
        2026,
        9,
        3,
        12,
        0,
        tzinfo=timezone.utc,
    )

    result = service.expire_booking(booking)

    assert result is booking
    assert booking.status == BookingStatus.EXPIRED
    assert booking.hold_expires_at is None


def test_expire_booking_rejects_non_held_booking():
    db = Mock()
    service = BookingService(db)

    booking = Mock()
    booking.status = BookingStatus.REQUESTED
    booking.hold_expires_at = None

    with pytest.raises(Exception, match="Invalid booking state transition"):
        service.expire_booking(booking)

    assert booking.status == BookingStatus.REQUESTED
    assert booking.hold_expires_at is None


def test_expire_booking_restores_hold_expiry_when_transition_fails():
    db = Mock()
    service = BookingService(db)

    booking = Mock()
    booking.status = BookingStatus.REQUESTED

    original_expiry = datetime(
        2026,
        9,
        3,
        12,
        0,
        tzinfo=timezone.utc,
    )
    booking.hold_expires_at = original_expiry

    with pytest.raises(Exception, match="Invalid booking state transition"):
        service.expire_booking(booking)

    assert booking.status == BookingStatus.REQUESTED
    assert booking.hold_expires_at == original_expiry
def test_reject_booking_moves_requested_to_rejected():
    db = Mock()
    service = BookingService(db)

    booking = Mock()
    booking.status = BookingStatus.REQUESTED
    booking.hold_expires_at = None

    result = service.reject_booking(booking)

    assert result is booking
    assert booking.status == BookingStatus.REJECTED
    assert booking.hold_expires_at is None


def test_reject_booking_moves_held_to_rejected_and_clears_hold_expiry():
    db = Mock()
    service = BookingService(db)

    booking = Mock()
    booking.status = BookingStatus.HELD
    booking.hold_expires_at = datetime(
        2026,
        9,
        3,
        12,
        0,
        tzinfo=timezone.utc,
    )

    result = service.reject_booking(booking)

    assert result is booking
    assert booking.status == BookingStatus.REJECTED
    assert booking.hold_expires_at is None


def test_reject_booking_rejects_confirmed_booking():
    db = Mock()
    service = BookingService(db)

    booking = Mock()
    booking.status = BookingStatus.CONFIRMED
    booking.hold_expires_at = None

    with pytest.raises(Exception, match="Invalid booking state transition"):
        service.reject_booking(booking)

    assert booking.status == BookingStatus.CONFIRMED
    assert booking.hold_expires_at is None


def test_reject_booking_restores_hold_expiry_when_transition_fails():
    db = Mock()
    service = BookingService(db)

    booking = Mock()
    booking.status = BookingStatus.CONFIRMED

    original_expiry = datetime(
        2026,
        9,
        3,
        12,
        0,
        tzinfo=timezone.utc,
    )
    booking.hold_expires_at = original_expiry

    with pytest.raises(Exception, match="Invalid booking state transition"):
        service.reject_booking(booking)

    assert booking.status == BookingStatus.CONFIRMED
    assert booking.hold_expires_at == original_expiry
def test_start_booking_moves_confirmed_to_in_progress():
    db = Mock()
    service = BookingService(db)

    booking = Mock()
    booking.status = BookingStatus.CONFIRMED

    result = service.start_booking(booking)

    assert result.from_status == BookingStatus.CONFIRMED
    assert result.to_status == BookingStatus.IN_PROGRESS
    assert booking.status == BookingStatus.IN_PROGRESS


def test_start_booking_rejects_non_confirmed_booking():
    db = Mock()
    service = BookingService(db)

    booking = Mock()
    booking.status = BookingStatus.HELD

    with pytest.raises(Exception, match="Invalid booking state transition"):
        service.start_booking(booking)

    assert booking.status == BookingStatus.HELD


def test_start_booking_does_not_commit():
    db = Mock()
    service = BookingService(db)

    booking = Mock()
    booking.status = BookingStatus.CONFIRMED

    service.start_booking(booking)

    db.commit.assert_not_called()
