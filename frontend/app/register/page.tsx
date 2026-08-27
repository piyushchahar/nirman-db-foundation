import Link from "next/link";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export default function RegisterPage() {
  return (
    <main className="flex min-h-screen items-center justify-center px-6">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="text-2xl">Create your account</CardTitle>
          <CardDescription>
            Registration isn&apos;t open yet — we&apos;re still building it.
          </CardDescription>
        </CardHeader>

        <CardContent>
          <p className="text-sm text-muted-foreground">
            Already have an account?
          </p>
          <Link
            href="/login"
            className={cn(buttonVariants({ variant: "default" }), "mt-4 w-full")}
          >
            Go to login
          </Link>
        </CardContent>
      </Card>
    </main>
  );
}
