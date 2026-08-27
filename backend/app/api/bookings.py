from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.booking_service import BookingService


router = APIRouter(prefix="/bookings", tags=["bookings"])


class CreateBookingRequest(BaseModel):
    job_requirement_id: UUID
    requester_id: UUID
    idempotency_key: str


@router.post("")
def create_booking(
    request: CreateBookingRequest,
    db: Session = Depends(get_db),
):
    service = BookingService(db)

    booking = service.create_booking_idempotent(
        requester_id=request.requester_id,
        job_requirement_id=request.job_requirement_id,
        idempotency_key=request.idempotency_key,
        request_data={
            "job_requirement_id": str(request.job_requirement_id),
        },
    )

    db.commit()

    return {
        "id": str(booking.id),
        "job_requirement_id": str(booking.job_requirement_id),
        "requester_id": str(booking.requester_id),
        "status": booking.status.value,
    }
