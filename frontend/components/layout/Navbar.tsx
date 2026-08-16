import Link from "next/link";

export function Navbar() {
  return (
    <nav className="border-b bg-background">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
        <Link href="/" className="text-xl font-bold tracking-tight">
          NIRMAN
        </Link>

        <div className="flex items-center gap-6">
          <Link
            href="/login"
            className="text-sm font-medium hover:underline"
          >
            Login
          </Link>

          <Link
            href="/register"
            className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90"
          >
            Register
          </Link>
        </div>
      </div>
    </nav>
  );
}