"use client";

import { ReactNode, useState } from "react";
import { Navbar } from "./Navbar";
import { Sidebar, type SidebarItem } from "./Sidebar";

type DashboardLayoutProps = {
  children: ReactNode;
  sidebarItems: SidebarItem[];
};

export function DashboardLayout({ children, sidebarItems }: DashboardLayoutProps) {
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  return (
    <div className="min-h-screen bg-background">
      <Navbar
        onMenuToggle={() => setMobileNavOpen((open) => !open)}
        isMenuOpen={mobileNavOpen}
      />

      <div className="flex min-h-[calc(100vh-4rem)]">
        <Sidebar
          items={sidebarItems}
          isOpen={mobileNavOpen}
          onClose={() => setMobileNavOpen(false)}
        />

        <main className="min-w-0 flex-1 p-4 sm:p-6 lg:p-8">{children}</main>
      </div>
    </div>
  );
}
