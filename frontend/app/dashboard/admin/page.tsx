import Link from "next/link";
import { notFound } from "next/navigation";

import { AdminConsole } from "@/src/components/features/admin/AdminConsole";
import { getSessionToken } from "@/src/lib/auth/session";

export const metadata = { title: "Admin console · SIGNAL" };
export const dynamic = "force-dynamic";

// System-level admin console: providers & credentials (ADR-10), children
// oversight, staff management, tamper-evident audit trail, usage.
// Non-admins get an access-error state inside the console.
export default async function AdminConsolePage() {
  const token = await getSessionToken();
  if (!token) {
    notFound();
  }

  return (
    <main className="mx-auto w-full max-w-5xl p-6 sm:p-8">
      <Link href="/dashboard" className="text-sm font-medium text-pine hover:underline">
        ← Back to dashboard
      </Link>
      <h1 className="mt-4 font-display text-3xl font-bold tracking-tight text-ink">
        Admin console
      </h1>
      <p className="mt-2 max-w-2xl text-sm leading-relaxed text-ink-soft">
        System-level administration. Keys are stored encrypted and are
        write-only — after saving, only the last four characters are ever
        shown. An active stored key (and model) takes precedence over the
        environment; removing it falls back to the environment.
      </p>

      <div className="mt-6">
        <AdminConsole />
      </div>
    </main>
  );
}
