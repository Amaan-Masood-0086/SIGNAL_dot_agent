import Link from "next/link";
import { redirect } from "next/navigation";

import { Badge } from "@/src/components/ui/Badge";
import { Button } from "@/src/components/ui/Button";
import { Card, CardBody } from "@/src/components/ui/Card";
import { listChildren } from "@/src/lib/api/children";
import { getSessionToken } from "@/src/lib/auth/session";

export const metadata = { title: "Dashboard — SIGNAL" };
export const dynamic = "force-dynamic";

export default async function DashboardPage() {
  const token = await getSessionToken();
  if (!token) {
    redirect("/login");
  }

  let roster;
  try {
    roster = await listChildren(token, 1, 100);
  } catch {
    roster = null;
  }

  return (
    <main className="mx-auto w-full max-w-5xl p-6 sm:p-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-xs font-semibold tracking-[0.14em] text-ink-soft uppercase">
            Your institution
          </p>
          <h1 className="mt-1 font-display text-3xl font-bold tracking-tight text-ink">
            Children
          </h1>
        </div>
        <Link href="/dashboard/children/new">
          <Button aria-label="Register a child">Register a child</Button>
        </Link>
      </div>
      <div className="mt-2">
        {/* Admin surface (system-level role): provider status + credential
            management. Non-admins see an access-error state on the page. */}
        <Link
          href="/dashboard/admin"
          className="text-sm font-medium text-pine hover:underline"
        >
          Admin: providers & credentials →
        </Link>
      </div>

      <div className="mt-6">
        {roster === null ? (
          <Card>
            <CardBody>
              <p className="text-sm text-ink-soft">
                The child roster could not be loaded right now. Refresh the
                page, or register a child directly.
              </p>
            </CardBody>
          </Card>
        ) : roster.items.length === 0 ? (
          <Card>
            <CardBody>
              <p className="font-display text-lg font-semibold text-ink">
                No children registered yet
              </p>
              <p className="mt-2 max-w-md text-sm leading-relaxed text-ink-soft">
                Register a child to start an observation session. Intake
                captures whether the date of birth is confirmed or estimated
                — this directly affects how confidence is graded later.
              </p>
              <div className="mt-4">
                <Link href="/dashboard/children/new">
                  <Button aria-label="Register your first child">
                    Register your first child
                  </Button>
                </Link>
              </div>
            </CardBody>
          </Card>
        ) : (
          <>
            <p className="text-sm text-ink-soft">
              {roster.total} {roster.total === 1 ? "child" : "children"} registered
            </p>
            <ul className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2">
              {roster.items.map((child) => (
                <li key={child.id}>
                  <Link
                    href={`/dashboard/children/${child.id}`}
                    className="group flex h-full flex-col gap-3 rounded-xl border border-line bg-surface p-5 transition-colors duration-150 hover:border-pine/50 hover:bg-moss/40 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-pine"
                    aria-label={`Open profile for ${child.name}`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <span className="font-display text-lg font-semibold tracking-tight text-ink group-hover:text-pine-deep">
                        {child.name}
                      </span>
                      <Badge tone={child.dob_confirmed ? "neutral" : "warning"}>
                        {child.dob_confirmed ? "Confirmed DOB" : "Estimated age"}
                      </Badge>
                    </div>
                    <div className="mt-auto flex items-center justify-between text-xs text-ink-soft">
                      <span>
                        {child.dob_confirmed
                          ? `Born ${child.dob}`
                          : `Age ${child.estimated_age_range ?? "—"}`}
                        {" · "}Intake {child.intake_date}
                      </span>
                      <span
                        aria-hidden="true"
                        className="font-semibold text-pine transition-transform duration-150 group-hover:translate-x-0.5"
                      >
                        Open profile →
                      </span>
                    </div>
                  </Link>
                </li>
              ))}
            </ul>
          </>
        )}
      </div>
    </main>
  );
}
