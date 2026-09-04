import Link from "next/link";
import type { ReactNode } from "react";

import { Button } from "@/src/components/ui/Button";
import { Icon } from "@/src/components/ui/Icon";
import { requireStaff } from "@/src/lib/auth/rbac";

export const dynamic = "force-dynamic";

/**
 * Gate for every `/dashboard/admin/*` surface.
 *
 * This is the UX half of a two-layer control: the backend re-checks the DB
 * staff row on every admin endpoint (`get_current_admin_staff`), so nothing
 * here grants access — it only stops a caretaker from being dropped into a
 * console that would 403 on every panel. Deny by default: anything other
 * than a live admin row renders the refusal.
 *
 * The refusal deliberately names no account. Telling a caretaker which
 * address holds admin would hand them half a credential pair.
 */
export default async function AdminLayout({ children }: { children: ReactNode }) {
  const me = await requireStaff();

  if (!me.is_admin) {
    return (
      <main className="mx-auto flex w-full max-w-2xl flex-1 items-center p-5 sm:p-8">
        <div className="w-full rounded-xl border border-line bg-surface p-8 text-center">
          <span className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-amber-soft text-amber">
            <Icon name="shield" className="h-6 w-6" />
          </span>
          <h1 className="mt-4 font-display text-2xl font-bold tracking-tight text-ink">
            Admin access required
          </h1>
          <p className="mx-auto mt-2 max-w-md text-sm leading-relaxed text-ink-soft">
            System administration — provider credentials, staff roles, the
            audit trail and cost reporting — is restricted to the
            system-level admin role. Your account is signed in as{" "}
            <span className="font-semibold text-ink">{me.role}</span>.
          </p>
          <p className="mx-auto mt-2 max-w-md text-xs leading-relaxed text-ink-soft">
            If you need this access, ask an existing administrator to grant it.
            Every role change is recorded in the audit log.
          </p>
          <div className="mt-6">
            <Link href="/dashboard">
              <Button aria-label="Back to children">Back to children</Button>
            </Link>
          </div>
        </div>
      </main>
    );
  }

  return <>{children}</>;
}
