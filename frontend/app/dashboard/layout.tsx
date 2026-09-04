import type { ReactNode } from "react";

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
      <div className="flex min-h-svh flex-col lg:flex-row">
        <SidebarNav
          groups={navGroupsFor(me.is_admin)}
          user={{
            email: me.email,
            role: me.role,
            institutionName: me.institution_name,
            isAdmin: me.is_admin,
          }}
        />
        <div className="flex min-w-0 flex-1 flex-col">{children}</div>
      </div>
    </QueryProvider>
  );
}
