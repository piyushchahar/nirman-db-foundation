"use client";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { PageHeader } from "@/components/layout/PageHeader";
import { EmptyState } from "@/components/dashboard/EmptyState";
import {
  LayoutDashboard,
  User,
  CalendarClock,
  ClipboardList,
} from "lucide-react";

const workerSidebarItems = [
  { label: "Dashboard", href: "/worker", icon: LayoutDashboard },
  { label: "Profile", href: "/worker/profile", icon: User },
  { label: "Availability", href: "/worker/availability", icon: CalendarClock },
  { label: "Bookings", href: "/worker/bookings", icon: ClipboardList },
];

export default function WorkerAvailabilityPage() {
  return (
    <DashboardLayout sidebarItems={workerSidebarItems}>
      <PageHeader
        title="Availability"
        description="Set the time windows you're available to work."
      />
      <EmptyState
        icon={CalendarClock}
        title="Availability scheduling is coming soon"
        description="This page is a placeholder. You'll be able to add concrete available time windows here."
      />
    </DashboardLayout>
  );
}
