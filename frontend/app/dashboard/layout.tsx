import Link from "next/link";
import { redirect } from "next/navigation";
import type { ReactNode } from "react";

import { LogoutButton } from "@/src/components/features/auth/LogoutButton";
import { QueryProvider } from "@/src/components/providers/QueryProvider";
import { GrowthCurve } from "@/src/components/ui/GrowthCurve";
import { getSessionToken } from "@/src/lib/auth/session";

// Auth guard + institution scope live HERE (web-development.md file
// structure). Server-side session check is the control; middleware is the
// redirect convenience.
export default async function DashboardLayout({ children }: { children: ReactNode }) {
  const token = await getSessionToken();
  if (!token) {
    redirect("/login");
  }

  return (
    <QueryProvider>
      <header className="border-b border-line bg-surface">
        <div className="mx-auto flex w-full max-w-5xl items-center justify-between px-6 py-3">
          <div className="flex items-center gap-6">
            <Link
              href="/dashboard"
              className="flex items-center gap-2.5"
              aria-label="SIGNAL dashboard"
            >
              <GrowthCurve className="h-6 w-20 text-pine" />
              <span className="font-display text-lg font-bold tracking-tight text-pine-deep">
                SIGNAL
              </span>
            </Link>
            <nav aria-label="Primary" className="flex items-center gap-4 text-sm font-medium">
              <Link
                href="/dashboard/children/new"
                className="rounded-md px-2 py-1 text-ink-soft transition-colors hover:bg-moss hover:text-ink"
              >
                Register a child
              </Link>
            </nav>
          </div>
          <LogoutButton />
        </div>
      </header>
      <div className="flex flex-1 flex-col">{children}</div>
    </QueryProvider>
  );
}
