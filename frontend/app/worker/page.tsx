import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { PageHeader } from "@/components/layout/PageHeader";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

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
        <PageHeader
          title="Worker Dashboard"
          description="Manage your profile, availability, and bookings."
        />

        <div className="mt-8 grid gap-4 md:grid-cols-3">
          <Card>
            <CardHeader>
              <CardTitle>Upcoming Bookings</CardTitle>
            </CardHeader>

            <CardContent>
              <p className="text-3xl font-bold">0</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Profile Views</CardTitle>
            </CardHeader>

            <CardContent>
              <p className="text-3xl font-bold">0</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Availability</CardTitle>
            </CardHeader>

            <CardContent>
              <p className="text-3xl font-bold">Set</p>
            </CardContent>
          </Card>
        </div>
      </div>
    </DashboardLayout>
  );
}