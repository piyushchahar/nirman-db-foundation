"use client";

interface BookingActionsProps {
  status: string;
}

export default function BookingActions({
  status,
}: BookingActionsProps) {
  return (
    <div className="flex gap-3">
      {status === "REQUESTED" && (
        <button className="rounded-lg border px-4 py-2 text-sm">
          Cancel Booking
        </button>
      )}

      {status === "HELD" && (
        <button className="rounded-lg border px-4 py-2 text-sm">
          Confirm Booking
        </button>
      )}

      {status === "CONFIRMED" && (
        <button className="rounded-lg border px-4 py-2 text-sm">
          Start Booking
        </button>
      )}

      {status === "IN_PROGRESS" && (
        <button className="rounded-lg border px-4 py-2 text-sm">
          Mark Complete
        </button>
      )}
    </div>
  );
}