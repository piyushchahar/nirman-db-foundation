from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.models.worker_reservation import WorkerReservation
from app.services.reservation_service import ReservationService


def test_create_reservation_adds_worker_reservation():
    db = MagicMock()
    service = ReservationService(db)

    worker_profile_id = uuid4()
    booking_id = uuid4()

    start_time = datetime(
        2026,
        9,
        1,
        9,
        0,
        tzinfo=timezone.utc,
    )
    end_time = datetime(
        2026,
        9,
        1,
        17,
        0,
        tzinfo=timezone.utc,
    )

    result = service.create_reservation(
        worker_profile_id=worker_profile_id,
        booking_id=booking_id,
        start_time=start_time,
        end_time=end_time,
    )

    assert isinstance(result, WorkerReservation)
    assert result.worker_profile_id == worker_profile_id
    assert result.booking_id == booking_id
    assert result.reservation_range is not None

    db.add.assert_called_once_with(result)
    db.flush.assert_called_once()


def test_create_reservation_rejects_naive_start_time():
    db = MagicMock()
    service = ReservationService(db)

    with pytest.raises(ValueError, match="timezone-aware"):
        service.create_reservation(
            worker_profile_id=uuid4(),
            booking_id=uuid4(),
            start_time=datetime(2026, 9, 1, 9, 0),
            end_time=datetime(
                2026,
                9,
                1,
                17,
                0,
                tzinfo=timezone.utc,
            ),
        )
