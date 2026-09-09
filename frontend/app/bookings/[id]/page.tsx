import BookingActions from "@/components/bookings/BookingActions";
import BookingStatusBadge from "@/components/bookings/BookingStatusBadge";

interface BookingDetailsPageProps {
  params: Promise<{ id: string }>;
}

export default async function BookingDetailsPage({
  params,
}: BookingDetailsPageProps) {
  const { id } = await params;

  return (
    <main className="min-h-screen p-8">
      <div className="mx-auto max-w-3xl">
        <div className="mb-8 flex items-start justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold">Booking Details</h1>
            <p className="mt-2 text-sm text-muted-foreground">
              Booking ID: {id}
            </p>
          </div>

          <BookingStatusBadge status="REQUESTED" />
        </div>

        <div className="rounded-xl border p-6">
          <h2 className="text-lg font-semibold">Booking Information</h2>

          <div className="mt-5 space-y-3 text-sm">
            <div className="flex justify-between gap-4">
              <span className="text-muted-foreground">
                Job Requirement
              </span>
              <span>Not loaded yet</span>
            </div>

            <div className="flex justify-between gap-4">
              <span className="text-muted-foreground">Requester</span>
              <span>Not loaded yet</span>
            </div>

            <div className="flex justify-between gap-4">
              <span className="text-muted-foreground">Status</span>
              <span>REQUESTED</span>
            </div>
          </div>

          <div className="mt-8 border-t pt-6">
            <BookingActions status="REQUESTED" />
          </div>
        </div>
      </div>
    </main>
  );
}