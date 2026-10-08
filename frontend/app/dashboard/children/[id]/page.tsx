import Link from "next/link";
import { notFound, redirect } from "next/navigation";
import { ArchiveChild } from "@/src/components/features/children/ArchiveChild";
import { ReasoningTrail } from "@/src/components/features/reasoning/ReasoningTrail";
import { PageHeader } from "@/src/components/layout/PageHeader";
import { Badge } from "@/src/components/ui/Badge";
import { Alert } from "@/src/components/ui/Alert";
import { Icon } from "@/src/components/ui/Icon";
import { StartSessionButton } from "@/src/components/features/children/StartSessionButton";
import { getChild, isAuthorizationError } from "@/src/lib/api/children";
import { listChildFlags } from "@/src/lib/api/flags";
import { createSession } from "@/src/lib/api/sessions";
import { requireStaff } from "@/src/lib/auth/rbac";
import { getSessionToken } from "@/src/lib/auth/session";
import { domainLabel, gradeBadgeTone, gradeMeta } from "@/src/lib/screening/grade";
export const metadata = { title: "Child profile | SIGNAL" };

async function startSession(childId: string, mode: "voice" | "text") {
  "use server";
  const me = await requireStaff();
  if (me.is_admin) redirect("/dashboard/admin");
  const token = (await getSessionToken()) ?? "";
  const child = await getChild(token, childId);
  if (child.archived_at) redirect(`/dashboard/children/${childId}`);
  const session = await createSession(token, { child_id: childId, mode });
  redirect(`/dashboard/sessions/${session.id}`);
}

export default async function ChildProfilePage({ params }: { params: Promise<{ id: string }> }) {
  const me = await requireStaff();
  if (me.is_admin) redirect("/dashboard/admin/children");
  const { id } = await params;
  const token = (await getSessionToken()) ?? "";
  let child;
  try { child = await getChild(token, id); } catch (error) { if (isAuthorizationError(error)) notFound(); throw error; }
  const history = await listChildFlags(token, id).catch(() => null);
  const archived = !!child.archived_at;
  return <main className="mx-auto w-full max-w-6xl p-5 sm:p-8">
    <Link href="/dashboard" className="text-xs font-semibold text-pine">← Back to children</Link>
    <div className="mt-5"><PageHeader eyebrow="Child record" title={child.name} lede="Observations, screening results and the context behind them." actions={<Badge tone={archived ? "warning" : "neutral"}>{archived ? "Archived record" : "Active record"}</Badge>} /></div>
    <div className="profile-layout">
      <div>
        {!archived && <section className="welcome-panel no-print" aria-label="Start an observation">
          <div><h2>Record an observation</h2><p>Describe what you noticed in your own words. Choose text, or speak and review the transcript.</p><div className="mt-5 flex flex-wrap gap-3"><form action={startSession.bind(null, child.id, "text")}><StartSessionButton mode="text" /></form><form action={startSession.bind(null, child.id, "voice")}><StartSessionButton mode="voice" /></form></div></div>
        </section>}
        <section className="mt-6 rounded-xl border border-line bg-surface">
          <header className="flex items-center justify-between border-b border-line p-5"><div><h2 className="font-display text-lg font-semibold">Screening history</h2><p className="mt-1 text-xs text-ink-soft">Each result keeps its explanation and reference sources.</p></div>{history && <Badge>{history.total} results</Badge>}</header>
          <div className="p-5">
            {history === null ? <Alert tone="danger">Screening history could not be loaded. Refresh to try again.</Alert> : history.items.length === 0 ? <div className="py-8 text-center"><Icon name="audit" className="mx-auto h-7 w-7 text-pine" /><p className="mt-3 font-semibold">No screening results yet</p><p className="mt-2 text-xs text-ink-soft">{archived ? "This archived record has no saved screening results." : "Start an observation above to create the first record."}</p></div> : <ul className="space-y-6">{history.items.map((flag, index) => {
              const meta = gradeMeta(flag.confidence_grade);
              return <li key={flag.id} className="border-b border-line pb-6 last:border-0 last:pb-0"><div className="flex flex-wrap items-center gap-2"><Badge tone={gradeBadgeTone(flag.confidence_grade)}>{meta ? `${meta.label} · ${meta.headline}` : flag.confidence_grade}</Badge><span className="text-xs text-ink-soft">{domainLabel(flag.domain) ?? flag.domain}</span><time className="ml-auto text-xs text-ink-soft" dateTime={flag.created_at}>{flag.created_at.slice(0,10)}</time></div>{flag.explanation_text && <p dir="auto" className="record-text mt-3 text-sm leading-relaxed">{flag.explanation_text}</p>}<details className="mt-4" open={index === 0}><summary className="cursor-pointer text-xs font-semibold text-pine">Review the evidence ({flag.reasoning_trail.length} references)</summary><div className="mt-3"><ReasoningTrail entries={flag.reasoning_trail} /></div></details><Link href={`/dashboard/sessions/${flag.session_id}`} className="mt-4 inline-flex text-xs font-semibold text-pine">Open observation session →</Link></li>;
            })}</ul>}
            {history && history.total > history.items.length && <p className="mt-4 text-xs text-ink-soft">Showing {history.items.length} of {history.total} results.</p>}
          </div>
        </section>
      </div>
      <aside className="profile-details">
        <h2 className="mb-5 font-display text-lg font-semibold">About this child</h2>
        <dl>
          <div><dt>Age information</dt><dd><Badge tone={child.dob_confirmed ? "neutral" : "warning"}>{child.dob_confirmed ? "Confirmed date of birth" : "Estimated age"}</Badge></dd></div>
          <div><dt>{child.dob_confirmed ? "Date of birth" : "Recorded age range"}</dt><dd>{child.dob_confirmed ? child.dob : child.estimated_age_range}</dd></div>
          {!child.dob_confirmed && <div><dt>Basis of estimate</dt><dd>{child.estimated_age_note ?? "Not recorded"}</dd></div>}
          <div><dt>Intake date</dt><dd>{child.intake_date}</dd></div>
        </dl>
        {!child.dob_confirmed && <p className="mt-5 rounded-lg bg-amber-soft p-3 text-xs leading-relaxed text-amber">Age uncertainty is taken into account when reviewing age-dependent milestones.</p>}
        <div className="no-print mt-6 border-t border-line pt-5"><ArchiveChild childId={child.id} childName={child.name} archivedReason={child.archived_reason} /><p className="mt-3 text-xs leading-relaxed text-ink-soft">Archiving removes a child from the active roster. Their history stays available.</p></div>
      </aside>
    </div>
  </main>;
}
