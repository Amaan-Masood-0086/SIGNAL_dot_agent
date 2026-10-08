import type { ReactNode } from "react";
import Link from "next/link";

import { SidebarNav } from "@/src/components/layout/SidebarNav";
import { navGroupsFor } from "@/src/components/layout/nav";
import { QueryProvider } from "@/src/components/providers/QueryProvider";
import { requireStaff } from "@/src/lib/auth/rbac";

// Auth guard + role resolution live HERE (web-development.md file structure).
// The server-side session check is the control; the proxy redirect is the
// convenience. `requireStaff()` also resolves the caller's role once per
// render, and the navigation is filtered from it — a caretaker's HTML never
// contains an admin link.
export default async function DashboardLayout({ children }: { children: ReactNode }) {
  const me = await requireStaff();

  return (
    <QueryProvider>
      <a href="#main-content" className="skip-link">Skip to content</a>
      <div className="app-shell">
        <SidebarNav
          groups={navGroupsFor(me.is_admin)}
          user={{
            email: me.email,
            role: me.role,
            institutionName: me.institution_name,
            isAdmin: me.is_admin,
          }}
        />
        <div className="app-content">
          <header className="workspace-header">
            <div><p>{me.is_admin ? "Administration" : "Care workspace"}</p><small>{me.is_admin ? "Manage teams, access and services" : me.institution_name ?? "Your institution"}</small></div>
            <div className="flex items-center gap-5"><span className="rounded-md bg-amber-soft px-2.5 py-1 text-xs text-amber">Synthetic data only</span><Link href="/dashboard/guide" className="hidden sm:inline-flex">Help & guidance</Link></div>
          </header>
          <div id="main-content" tabIndex={-1}>{children}</div>
        </div>
      </div>
    </QueryProvider>
  );
}
