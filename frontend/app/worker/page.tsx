import { DashboardLayout } from "@/components/layout/DashboardLayout";

const workerSidebarItems = [
  { label: "Dashboard", href: "/worker" },
  { label: "Profile", href: "/worker/profile" },
  { label: "Availability", href: "/worker/availability" },
  { label: "Bookings", href: "/worker/bookings" },
];

export default function WorkerDashboard() {
  return (
    <DashboardLayout sidebarItems={workerSidebarItems}>
      <div>
        <h1 className="text-3xl font-bold tracking-tight">
          Worker Dashboard
        </h1>

        <p className="mt-2 text-muted-foreground">
          Manage your profile, availability, and bookings.
        </p>

        <div className="mt-8 grid gap-4 md:grid-cols-3">
          <div className="rounded-lg border p-6">
            <p className="text-sm text-muted-foreground">
              Upcoming Bookings
            </p>
            <p className="mt-2 text-3xl font-bold">0</p>
          </div>

          <div className="rounded-lg border p-6">
            <p className="text-sm text-muted-foreground">
              Profile Views
            </p>
            <p className="mt-2 text-3xl font-bold">0</p>
          </div>

          <div className="rounded-lg border p-6">
            <p className="text-sm text-muted-foreground">
              Availability
            </p>
            <p className="mt-2 text-3xl font-bold">Set</p>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}