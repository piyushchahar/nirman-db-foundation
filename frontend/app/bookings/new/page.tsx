import BookingForm from "@/components/bookings/BookingForm";

export default function NewBookingPage() {
  return (
    <main className="min-h-screen p-8">
      <div className="mx-auto max-w-2xl">
        <div className="mb-8">
          <h1 className="text-3xl font-bold">Create a Booking</h1>
          <p className="mt-2 text-muted-foreground">
            Enter the details for your worker booking.
          </p>
        </div>

        <div className="rounded-xl border p-6">
          <BookingForm />
        </div>
      </div>
    </main>
  );
}