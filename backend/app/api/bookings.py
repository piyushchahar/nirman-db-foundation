from __future__ import annotations

from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.booking import Booking
from app.services.booking_service import BookingService


router = APIRouter(prefix="/api/v1/bookings", tags=["bookings"])


class CreateBookingRequest(BaseModel):
    job_requirement_id: UUID
    requester_id: UUID
    idempotency_key: str


class CancelBookingRequest(BaseModel):
    cancelled_by: UUID
    cancellation_reason: str


def success(data):
    return {
        "data": data,
        "meta": {"request_id": str(uuid4())},
    }


def get_booking_or_404(db: Session, booking_id: UUID) -> Booking:
    booking = db.get(Booking, booking_id)
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking


def booking_data(booking: Booking):
    return {
        "id": str(booking.id),
        "job_requirement_id": str(booking.job_requirement_id),
        "requester_id": str(booking.requester_id),
        "status": booking.status.value,
    }


@router.post("")
def create_booking(
    request: CreateBookingRequest,
    db: Session = Depends(get_db),
):
    try:
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
        return success(booking_data(booking))
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/{booking_id}/accept")
def accept_booking(
    booking_id: UUID,
    db: Session = Depends(get_db),
):
    booking = get_booking_or_404(db, booking_id)
    try:
        booking = BookingService(db).confirm_booking(booking)
        db.commit()
        return success(booking_data(booking))
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/{booking_id}/reject")
def reject_booking(
    booking_id: UUID,
    db: Session = Depends(get_db),
):
    booking = get_booking_or_404(db, booking_id)
    try:
        booking = BookingService(db).reject_booking(booking)
        db.commit()
        return success(booking_data(booking))
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/{booking_id}/start")
def start_booking(
    booking_id: UUID,
    db: Session = Depends(get_db),
):
    booking = get_booking_or_404(db, booking_id)
    try:
        booking = BookingService(db).start_booking(booking)
        db.commit()
        return success(booking_data(booking))
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/{booking_id}/mark-complete")
def mark_booking_complete(
    booking_id: UUID,
    db: Session = Depends(get_db),
):
    booking = get_booking_or_404(db, booking_id)
    try:
        booking = BookingService(db).mark_booking_complete(booking)
        db.commit()
        return success(booking_data(booking))
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/{booking_id}/confirm-complete")
def confirm_booking_complete(
    booking_id: UUID,
    db: Session = Depends(get_db),
):
    booking = get_booking_or_404(db, booking_id)
    try:
        booking = BookingService(db).confirm_booking_complete(booking)
        db.commit()
        return success(booking_data(booking))
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/{booking_id}/cancel")
def cancel_booking(
    booking_id: UUID,
    request: CancelBookingRequest,
    db: Session = Depends(get_db),
):
    booking = get_booking_or_404(db, booking_id)
    try:
        booking = BookingService(db).cancel_booking(
            booking=booking,
            cancelled_by=request.cancelled_by,
            cancellation_reason=request.cancellation_reason,
        )
        db.commit()
        return success(booking_data(booking))
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc))
