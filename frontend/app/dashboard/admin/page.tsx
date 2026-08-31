import Link from "next/link";
import { notFound } from "next/navigation";

import { AdminProvidersPanel } from "@/src/components/features/admin/AdminProvidersPanel";
import {
  listCredentials,
  listProviderStatuses,
  type CredentialStatus,
  type ProviderStatus,
} from "@/src/lib/api/admin";
import { getSessionToken } from "@/src/lib/auth/session";

export const metadata = { title: "Admin — providers · SIGNAL" };
export const dynamic = "force-dynamic";

// Admin panel: provider status + ADR-10 credential management (write-only).
// Non-admins get 403 from the backend — the panel then shows the error
// state rather than any data.
export default async function AdminProvidersPage() {
  const token = await getSessionToken();
  if (!token) {
    notFound();
  }

  let statuses: ProviderStatus[] = [];
  let credentials: CredentialStatus[] = [];
  let accessError: string | null = null;
  try {
    [statuses, credentials] = await Promise.all([
      listProviderStatuses(token),
      listCredentials(token),
    ]);
  } catch {
    accessError =
      "This page needs the admin role. Ask a system admin, or sign in with the seeded admin account.";
  }

  return (
    <main className="mx-auto w-full max-w-3xl p-6 sm:p-8">
      <Link href="/dashboard" className="text-sm font-medium text-pine hover:underline">
        ← Back to dashboard
      </Link>
      <h1 className="mt-4 font-display text-3xl font-bold tracking-tight text-ink">
        Providers & credentials
      </h1>
      <p className="mt-2 text-sm leading-relaxed text-ink-soft">
        Keys are stored encrypted and are write-only: after saving, only the
        last four characters are ever shown. An active stored key takes
        precedence over the environment variable; removing it falls back to
        the environment.
      </p>

      {accessError ? (
        <p className="mt-6 rounded-lg bg-red-soft p-4 text-sm font-medium text-red" role="alert">
          {accessError}
        </p>
      ) : (
        <div className="mt-6">
          <AdminProvidersPanel
            initialStatuses={statuses}
            initialCredentials={credentials}
          />
        </div>
      )}
    </main>
  );
}
