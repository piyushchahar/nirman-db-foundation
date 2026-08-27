"use client";

import Link from "next/link";
import { Menu, X } from "lucide-react";
import { Button, buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type NavbarProps = {
  onMenuToggle?: () => void;
  isMenuOpen?: boolean;
};

export function Navbar({ onMenuToggle, isMenuOpen }: NavbarProps) {
  return (
    <nav className="sticky top-0 z-30 border-b border-border bg-background">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6">
        <div className="flex items-center gap-2 sm:gap-3">
          {/* Only rendered when a page actually has a sidebar to toggle */}
          {onMenuToggle && (
            <Button
              variant="ghost"
              size="icon"
              className="lg:hidden"
              onClick={onMenuToggle}
              aria-label={isMenuOpen ? "Close menu" : "Open menu"}
              aria-expanded={isMenuOpen}
            >
              {isMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </Button>
          )}

          <Link
            href="/"
            className="flex items-center gap-2 rounded-md font-heading text-xl font-bold tracking-tight text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            <span className="flex h-7 w-7 items-center justify-center rounded-md bg-primary text-sm font-bold text-primary-foreground">
              N
            </span>
            <span className="hidden sm:inline">NIRMAN</span>
          </Link>
        </div>

        <div className="flex items-center gap-2 sm:gap-3">
          <Link
            href="/login"
            className={cn(buttonVariants({ variant: "ghost", size: "sm" }))}
          >
            Login
          </Link>
          <Link
            href="/register"
            className={cn(buttonVariants({ variant: "default", size: "sm" }))}
          >
            Register
          </Link>
        </div>
      </div>
    </nav>
  );
}
