import Link from "next/link";

import { ChildRoster } from "@/src/components/features/children/ChildRoster";
import { PageHeader } from "@/src/components/layout/PageHeader";
import { Alert } from "@/src/components/ui/Alert";
import { Button } from "@/src/components/ui/Button";
import { EmptyState } from "@/src/components/ui/EmptyState";
import { StatTile } from "@/src/components/ui/StatTile";
import { listChildren } from "@/src/lib/api/children";
import { requireStaff } from "@/src/lib/auth/rbac";
import { getSessionToken } from "@/src/lib/auth/session";

export const metadata = { title: "Children — SIGNAL" };
export const dynamic = "force-dynamic";

// The caretaker's home surface. Institution-scoped by the backend; the admin
// oversight roster is a separate route with its own gate and is reachable
// only from the Administration group in the sidebar.
export default async function DashboardPage() {
  const me = await requireStaff();
  const token = await getSessionToken();

  let roster;
  try {
    roster = token ? await listChildren(token, 1, 100) : null;
  } catch {
    roster = null;
  }

  const confirmed = roster?.items.filter((child) => child.dob_confirmed).length ?? 0;
  const estimated = (roster?.items.length ?? 0) - confirmed;

  return (
    <main className="mx-auto w-full max-w-6xl p-5 sm:p-8">
      <PageHeader
        eyebrow={me.institution_name ?? "Your institution"}
        title="Children"
        lede="Every child registered at your institution. Open a profile to start an observation session or review the screening history behind a flag."
        actions={
          <Link href="/dashboard/children/new">
            <Button aria-label="Register a child">Register a child</Button>
          </Link>
        }
      />

      {roster === null ? (
        <div className="mt-6">
          <Alert tone="danger">
            The child roster could not be loaded right now. Refresh the page, or
            register a child directly — the register form works independently.
          </Alert>
        </div>
      ) : roster.items.length === 0 ? (
        <div className="mt-6">
          <EmptyState
            icon="children"
            title="No children registered yet"
            description="Register a child to start an observation session. Intake captures whether the date of birth is confirmed or estimated — that choice directly affects how confidence is graded later."
            action={
              <Link href="/dashboard/children/new">
                <Button aria-label="Register your first child">
                  Register your first child
                </Button>
              </Link>
            }
          />
        </div>
      ) : (
        <>
          <div className="mt-6 grid grid-cols-2 gap-3 lg:grid-cols-4">
            <StatTile
              label="Registered"
              value={roster.total}
              hint="Children at your institution"
              tone="pine"
            />
            <StatTile
              label="Confirmed DOB"
              value={confirmed}
              hint="Age-dependent checks graded at full confidence"
            />
            <StatTile
              label="Estimated age"
              value={estimated}
              hint="Milestone confidence is downgraded automatically"
              tone={estimated > 0 ? "amber" : "neutral"}
            />
            <StatTile
              label="Access"
              value={me.is_admin ? "Admin" : "Caretaker"}
              hint={
                me.is_admin
                  ? "System-level tools are in the Administration menu"
                  : "Scoped to this institution only"
              }
            />
          </div>

          <div className="mt-6">
            <ChildRoster items={roster.items} />
          </div>
        </>
      )}
    </main>
  );
}
