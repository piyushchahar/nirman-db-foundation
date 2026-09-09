import Link from "next/link";

export default function HomePage() {
  return (
    <main className="min-h-screen p-8">
      <div className="mx-auto max-w-5xl">
        <div className="mb-10">
          <h1 className="text-4xl font-bold tracking-tight">Nirman</h1>
          <p className="mt-2 text-muted-foreground">
            Book and manage construction workers for your projects.
          </p>
        </div>

        <div className="max-w-xl">
          <Link
            href="/bookings/new"
            className="rounded-xl border p-6 transition hover:bg-muted"
          >
            <h2 className="text-xl font-semibold">Create a Booking</h2>
            <p className="mt-2 text-sm text-muted-foreground">
              Request a worker for your construction project.
            </p>
          </Link>

        </div>
      </div>
    </main>
  );
}