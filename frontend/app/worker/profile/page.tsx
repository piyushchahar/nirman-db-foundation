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

export default function WorkerProfilePage() {
  return (
    <DashboardLayout sidebarItems={workerSidebarItems}>
      <PageHeader
        title="Profile"
        description="Manage how clients see you on Nirman."
      />
      <EmptyState
        icon={User}
        title="Profile editing is coming soon"
        description="This page is a placeholder. Skills, rates, and profile details will be editable here."
      />
    </DashboardLayout>
  );
}
