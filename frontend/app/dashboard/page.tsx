import Link from "next/link";
import { redirect } from "next/navigation";
import { ChildRoster } from "@/src/components/features/children/ChildRoster";
import { PageHeader } from "@/src/components/layout/PageHeader";
import { Alert } from "@/src/components/ui/Alert";
import { buttonClass } from "@/src/components/ui/Button";
import { EmptyState } from "@/src/components/ui/EmptyState";
import { Icon } from "@/src/components/ui/Icon";
import { StatTile } from "@/src/components/ui/StatTile";
import { listChildren } from "@/src/lib/api/children";
import { requireStaff } from "@/src/lib/auth/rbac";
import { getSessionToken } from "@/src/lib/auth/session";
export const metadata = { title: "Care overview | SIGNAL" };
export const dynamic = "force-dynamic";

export default async function DashboardPage() {
  const me = await requireStaff();
  if (me.is_admin) redirect("/dashboard/admin");
  const token = (await getSessionToken()) ?? "";
  const [activeResult, archiveResult] = await Promise.allSettled([listChildren(token, 1, 100), listChildren(token, 1, 100, "archived")]);
  const roster = activeResult.status === "fulfilled" ? activeResult.value : null;
  const archived = archiveResult.status === "fulfilled" ? archiveResult.value : null;
  const confirmed = roster?.items.filter(child => child.dob_confirmed).length ?? 0;
  const estimated = (roster?.items.length ?? 0) - confirmed;
  const partial = !!roster && roster.total > roster.items.length;
  return <main className="mx-auto w-full max-w-6xl p-5 sm:p-8">
    <PageHeader eyebrow={me.institution_name ?? "Your institution"} title="Care overview" lede="A little attention today can make a lasting difference." actions={<Link href="/dashboard/children/new" className={buttonClass()}><Icon name="add-child" className="h-4 w-4" />Register a child</Link>} />
    <section className="welcome-panel mt-7" aria-label="Start here">
      <div><h2>What have you noticed today?</h2><p>Choose a child below, then describe what you have seen or heard. SIGNAL helps you turn that observation into a clear, reviewable record.</p></div>
      <Link href="/dashboard/guide" className={buttonClass("secondary")}>How screening works <Icon name="chevron-right" className="h-4 w-4" /></Link>
    </section>
    <div className="my-6 grid grid-cols-2 gap-3 lg:grid-cols-4">
      <StatTile label="Active children" value={roster?.total ?? "—"} hint="On your institution’s roster" tone="pine" />
      <StatTile label="Confirmed date of birth" value={roster ? confirmed : "—"} hint={partial ? "Among 100 loaded records" : "A documented date of birth"} />
      <StatTile label="Estimated age" value={roster ? estimated : "—"} hint={partial ? "Among 100 loaded records" : "Age uncertainty stays visible"} tone={estimated ? "amber" : "neutral"} />
      <StatTile label="Archived records" value={archived?.total ?? "—"} hint="History kept for continuity" />
    </div>
    {roster === null ? <Alert tone="danger">Children could not be loaded. Refresh to try again. You can still open the registration form.</Alert> : roster.items.length === 0 && archived?.total === 0 ? <EmptyState icon="children" title="Start with your first child" description="Create a profile with a documented date of birth or an estimated age. You can then record your first observation." action={<Link href="/dashboard/children/new" className={buttonClass()}>Register a child</Link>} /> : <ChildRoster items={roster.items} total={roster.total} archived={archived?.items ?? []} archivedTotal={archived?.total ?? 0} archivedUnavailable={archived === null} />}
    <p className="mt-5 flex items-center gap-2 text-xs leading-relaxed text-ink-soft"><Icon name="shield" className="h-4 w-4 shrink-0" />Screening supports a professional assessment. It does not provide a diagnosis.</p>
  </main>;
}
