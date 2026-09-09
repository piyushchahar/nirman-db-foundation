import { apiFetch } from "./api";
import type { Booking } from "@/types/booking";

export async function getBooking(id: string): Promise<Booking> {
  return apiFetch<Booking>(`/bookings/${id}`);
}