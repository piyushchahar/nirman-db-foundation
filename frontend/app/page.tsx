import { Navbar } from "@/components/layout/Navbar";

export default function Home() {
  return (
    <div className="min-h-screen">
      <Navbar />

      <main className="flex min-h-[calc(100vh-4rem)] flex-col items-center justify-center px-6">
        <div className="max-w-3xl text-center">
          <h1 className="text-5xl font-bold tracking-tight">
            NIRMAN
          </h1>

          <p className="mt-6 text-xl text-muted-foreground">
            Find trusted workers and get your work done.
          </p>

          <div className="mt-8 flex justify-center gap-4">
            <button className="rounded-md bg-primary px-6 py-3 text-primary-foreground">
              Get Started
            </button>

            <button className="rounded-md border px-6 py-3">
              Login
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}