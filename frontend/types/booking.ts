export type BookingStatus =
  | "REQUESTED"
  | "HELD"
  | "CONFIRMED"
  | "IN_PROGRESS"
  | "COMPLETED"
  | "REJECTED"
  | "EXPIRED"
  | "CANCELLED";

export interface Booking {
  id: string;
  job_requirement_id: string;
  requester_id: string;
  status: BookingStatus;

  team_booking_group_id: string | null;

  hold_expires_at: string | null;
  marked_complete_by_worker_at: string | null;
  confirmed_complete_by_homeowner_at: string | null;

  cancelled_by: string | null;
  cancellation_reason: string | null;
  cancelled_at: string | null;

  created_at: string;
  updated_at: string;
}