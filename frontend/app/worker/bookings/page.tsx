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

export default function WorkerBookingsPage() {
  return (
    <DashboardLayout sidebarItems={workerSidebarItems}>
      <PageHeader
        title="Bookings"
        description="Track requests and jobs booked with you."
      />
      <EmptyState
        icon={ClipboardList}
        title="Bookings tracking is coming soon"
        description="This page is a placeholder. Booking requests and their status will appear here."
      />
    </DashboardLayout>
  );
}
