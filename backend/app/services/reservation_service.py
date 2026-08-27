from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.models.worker_reservation import WorkerReservation


class ReservationService:
    """Application service for individual worker reservations."""

    def __init__(self, db: Session):
        self.db = db

    def create_reservation(
        self,
        *,
        worker_profile_id,
        booking_id,
        start_time: datetime,
        end_time: datetime,
    ):
        if start_time.tzinfo is None or end_time.tzinfo is None:
            raise ValueError("start_time and end_time must be timezone-aware")

        if end_time <= start_time:
            raise ValueError("end_time must be after start_time")

        reservation = WorkerReservation(
            worker_profile_id=worker_profile_id,
            booking_id=booking_id,
        )

        reservation.reservation_range = (
            f"[{start_time.isoformat()},{end_time.isoformat()})"
        )

        self.db.add(reservation)
        self.db.flush()

        return reservation
