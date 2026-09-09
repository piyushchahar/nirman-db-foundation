import type { BookingStatus } from "@/types/booking";

interface BookingStatusBadgeProps {
  status: BookingStatus;
}

export default function BookingStatusBadge({
  status,
}: BookingStatusBadgeProps) {
  return (
    <span className="rounded-full border px-3 py-1 text-xs font-medium">
      {status.replace("_", " ")}
    </span>
  );
}