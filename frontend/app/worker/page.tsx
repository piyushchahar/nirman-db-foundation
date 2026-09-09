"use client";
import Link from "next/link";
import {
  LayoutDashboard,
  User,
  CalendarClock,
  ClipboardList,
  CalendarCheck,
  Eye,
  CalendarPlus,
} from "lucide-react";

import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { PageHeader } from "@/components/layout/PageHeader";
import { EmptyState } from "@/components/dashboard/EmptyState";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const workerSidebarItems = [
  { label: "Dashboard", href: "/worker", icon: LayoutDashboard },
  { label: "Profile", href: "/worker/profile", icon: User },
  { label: "Availability", href: "/worker/availability", icon: CalendarClock },
  { label: "Bookings", href: "/worker/bookings", icon: ClipboardList },
];

// Mock data only — no backend calls. Shaped like what a real dashboard
// summary endpoint would eventually return, so swapping this for a real
// fetch later is a substitution, not a rewrite.
const stats = {
  upcomingBookings: 0,
  profileViews: 0,
  availabilityWindowsThisWeek: 0,
};

const quickActions = [
  {
    label: "Edit profile",
    description: "Update your skills, rates, and details.",
    href: "/worker/profile",
    icon: User,
  },
  {
    label: "Manage availability",
    description: "Add the windows you're free to work.",
    href: "/worker/availability",
    icon: CalendarClock,
  },
  {
    label: "View bookings",
    description: "See requests and jobs booked with you.",
    href: "/worker/bookings",
    icon: ClipboardList,
  },
];

export default function WorkerDashboard() {
  return (
    <DashboardLayout sidebarItems={workerSidebarItems}>
      <PageHeader
        title="Worker Dashboard"
        description="Manage your profile, availability, and bookings."
        action={
          <Link
            href="/worker/availability"
            className={cn(buttonVariants({ variant: "outline", size: "sm" }))}
          >
            <CalendarPlus className="h-4 w-4" aria-hidden="true" />
            Update availability
          </Link>
        }
      />

      {/* Quick actions */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {quickActions.map((action) => {
          const Icon = action.icon;
          return (
            <Link
              key={action.href}
              href={action.href}
              className="group flex items-start gap-3 rounded-xl border border-border bg-card p-4 transition-colors hover:border-primary/40 hover:bg-accent/40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
                <Icon className="h-4 w-4" aria-hidden="true" />
              </span>
              <span>
                <span className="block text-sm font-medium text-foreground">
                  {action.label}
                </span>
                <span className="mt-0.5 block text-xs text-muted-foreground">
                  {action.description}
                </span>
              </span>
            </Link>
          );
        })}
      </div>

      {/* Stat cards */}
      <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-muted-foreground">
              <CalendarCheck className="h-4 w-4" aria-hidden="true" />
              Upcoming Bookings
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-foreground">
              {stats.upcomingBookings}
            </p>
            <p className="mt-2 text-sm text-muted-foreground">
              No bookings yet. They&apos;ll show up here once a client hires you.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-muted-foreground">
              <Eye className="h-4 w-4" aria-hidden="true" />
              Profile Views
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-foreground">
              {stats.profileViews}
            </p>
            <p className="mt-2 text-sm text-muted-foreground">
              Complete your profile to start showing up in worker searches.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-muted-foreground">
              <CalendarClock className="h-4 w-4" aria-hidden="true" />
              Availability This Week
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-foreground">
              {stats.availabilityWindowsThisWeek}
            </p>
            <p className="mt-2 text-sm text-muted-foreground">
              No windows scheduled. Add your available hours below.
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Availability section */}
      <div className="mt-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Availability</CardTitle>
          </CardHeader>
          <CardContent>
            <EmptyState
              icon={CalendarClock}
              title="No availability windows set"
              description="Add the days and times you're free to work so clients can see when to book you."
              action={
                <Link
                  href="/worker/availability"
                  className={cn(buttonVariants({ variant: "default", size: "sm" }))}
                >
                  Add availability
                </Link>
              }
            />
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}