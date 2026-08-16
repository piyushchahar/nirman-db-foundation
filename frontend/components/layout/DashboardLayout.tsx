import { ReactNode } from "react";
import { Navbar } from "./Navbar";
import { Sidebar } from "./Sidebar";

type SidebarItem = {
  label: string;
  href: string;
};

type DashboardLayoutProps = {
  children: ReactNode;
  sidebarItems: SidebarItem[];
};

export function DashboardLayout({
  children,
  sidebarItems,
}: DashboardLayoutProps) {
  return (
    <div className="min-h-screen">
      <Navbar />

      <div className="flex min-h-[calc(100vh-4rem)]">
        <Sidebar items={sidebarItems} />

        <main className="flex-1 p-6">
          {children}
        </main>
      </div>
    </div>
  );
}