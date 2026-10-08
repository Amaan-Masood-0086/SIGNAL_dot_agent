import Link from "next/link";
import { PageHeader } from "@/src/components/layout/PageHeader";
import { buttonClass } from "@/src/components/ui/Button";
import { requireStaff } from "@/src/lib/auth/rbac";

export const metadata = { title: "Workspace guide | SIGNAL" };

export default async function GuidePage() {
  const me = await requireStaff();
  const steps = me.is_admin ? [
    ["Set up your team", "Create staff accounts for the correct institution. Caretakers see their institution’s children; administrators have system-wide access.", "/dashboard/admin/staff", "Manage staff"],
    ["Check service connections", "Review speech and reasoning providers. Store credentials and test a connection when required; a test can make a paid provider call.", "/dashboard/admin/providers", "Manage providers"],
    ["Review accountability", "Use the audit log to review recorded actions and check the integrity of the record. Usage reporting shows recorded costs and unpriced calls.", "/dashboard/admin/audit", "Open audit log"],
  ] : [
    ["Create a child’s profile", "Use a documented date of birth when available. Otherwise enter an estimated age range and describe its basis.", "/dashboard/children/new", "Register a child"],
    ["Describe what you noticed", "Open the child’s profile and start a text or voice session. Describe your own observations. Review a voice transcript before submitting it.", "/dashboard", "Find a child"],
    ["Read the result and its basis", "Answer the follow-up question if you can. If you do not know, say so. Each saved screening result has its explanation and source references on the child’s profile.", "/dashboard", "Open child records"],
  ];
  return <main className="mx-auto w-full max-w-4xl p-5 sm:p-8">
    <PageHeader eyebrow={me.is_admin ? "Administrator guide" : "Caretaker guide"} title="A clear next step" lede="A quick guide to the tools available in your workspace." />
    <div className="mt-8 space-y-5">{steps.map(([title, copy, href, label], index) => <section key={title} className="flex gap-5 rounded-xl border border-line bg-surface p-6"><span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-moss text-sm font-semibold text-pine">{index + 1}</span><div><h2 className="font-display text-lg font-semibold">{title}</h2><p className="mt-2 text-sm leading-relaxed text-ink-soft">{copy}</p><Link href={href} className="mt-4 inline-flex text-sm font-semibold text-pine">{label} →</Link></div></section>)}</div>
    {!me.is_admin && <section className="mt-6 rounded-xl bg-moss p-6"><h2 className="font-semibold">Before you finish a session</h2><p className="mt-2 text-sm leading-relaxed text-ink-soft">“Ask SIGNAL” saves and screens an observation. “Just save it” records the observation without screening. Saved observations stay in the session; text still in the input box is not saved. Screening supports professional review and does not establish a diagnosis.</p></section>}
    <Link href={me.is_admin ? "/dashboard/admin" : "/dashboard"} className={buttonClass("secondary", "mt-6")}>Back to overview</Link>
  </main>;
}
