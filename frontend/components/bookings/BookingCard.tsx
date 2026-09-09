import type { Booking } from "@/types/booking";
import BookingStatusBadge from "./BookingStatusBadge";

interface BookingCardProps {
  booking: Booking;
}

export default function BookingCard({ booking }: BookingCardProps) {
  return (
    <div className="rounded-xl border p-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="font-semibold">Booking</h3>
          <p className="mt-1 text-sm text-muted-foreground">
            ID: {booking.id}
          </p>
        </div>

        <BookingStatusBadge status={booking.status} />
      </div>

      <div className="mt-4 text-sm text-muted-foreground">
        <p>Job Requirement: {booking.job_requirement_id}</p>
        <p className="mt-1">Created: {booking.created_at}</p>
      </div>
    </div>
  );
}