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
