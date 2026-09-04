import Link from "next/link";
import { notFound, redirect } from "next/navigation";

import { ArchiveChild } from "@/src/components/features/children/ArchiveChild";
import { ReasoningTrail } from "@/src/components/features/reasoning/ReasoningTrail";
import { PageHeader } from "@/src/components/layout/PageHeader";
import { Badge } from "@/src/components/ui/Badge";
import { Button } from "@/src/components/ui/Button";
import { Card, CardBody, CardTitle } from "@/src/components/ui/Card";
import { getChild, isAuthorizationError } from "@/src/lib/api/children";
import { listChildFlags } from "@/src/lib/api/flags";
import type { FlagRead } from "@/src/lib/api/schemas";
import { createSession } from "@/src/lib/api/sessions";
import { getSessionToken } from "@/src/lib/auth/session";
import { domainLabel, gradeBadgeTone, gradeMeta } from "@/src/lib/screening/grade";

export const metadata = { title: "Child profile — SIGNAL" };

// FEAT-03 entry point: mode is chosen here; both modes produce the same
// downstream observation format — the choice only affects capture, not data.
async function startSession(childId: string, mode: "voice" | "text") {
  "use server";
  const token = await getSessionToken();
  if (!token) {
    redirect("/login");
  }
  const session = await createSession(token, { child_id: childId, mode });
  redirect(`/dashboard/sessions/${session.id}`);
}

// MUST #9: loading + error + empty states handled — loading.tsx and
// error.tsx sit alongside this page; auth/absence failures route to notFound.
export default async function ChildProfilePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const token = await getSessionToken();
  if (!token) {
    notFound();
  }

  let child;
  try {
    child = await getChild(token, id);
  } catch (error) {
    if (isAuthorizationError(error)) {
      notFound();
    }
    throw error;
  }

  // FEAT-09: screening history — flags are institution-scoped server-side;
  // an absent/failed flags surface must not block the profile itself.
  let flags: FlagRead[] = [];
  try {
    flags = (await listChildFlags(token, id)).items;
  } catch {
    flags = [];
  }

  return (
    <main className="mx-auto w-full max-w-3xl p-5 sm:p-8">
      <Link
        href="/dashboard"
        className="inline-flex text-sm font-medium text-pine hover:underline"
      >
        ← All children
      </Link>

      <div className="mt-3">
        <PageHeader
          eyebrow="Child profile"
          title={child.name}
          actions={
            <Badge tone={child.dob_confirmed ? "neutral" : "warning"}>
              {child.dob_confirmed ? "Confirmed DOB" : "Estimated age"}
            </Badge>
          }
        />
      </div>

      <Card className="mt-6">
        <CardTitle>Profile</CardTitle>
        <CardBody>
          <dl className="grid grid-cols-1 gap-x-6 gap-y-4 text-sm sm:grid-cols-2">
            {child.dob_confirmed ? (
              <div>
                <dt className="font-medium text-ink-soft">Date of birth</dt>
                <dd className="mt-1 font-semibold text-ink">{child.dob ?? "—"}</dd>
              </div>
            ) : (
              <>
                <div>
                  <dt className="font-medium text-ink-soft">Estimated age range</dt>
                  <dd className="mt-1 font-semibold text-ink">
                    {child.estimated_age_range ?? "—"}
                  </dd>
                </div>
                <div>
                  <dt className="font-medium text-ink-soft">Estimate basis</dt>
                  <dd className="mt-1 text-ink">
                    {child.estimated_age_note ?? "—"}
                  </dd>
                </div>
              </>
            )}
            <div>
              <dt className="font-medium text-ink-soft">Intake date</dt>
              <dd className="mt-1 text-ink">{child.intake_date}</dd>
            </div>
          </dl>
          {!child.dob_confirmed && (
            <p className="mt-4 rounded-lg bg-amber-soft p-3 text-xs leading-relaxed font-medium text-amber">
              Age is estimated. Any age-dependent milestone check will have its
              confidence grade downgraded automatically.
            </p>
          )}
        </CardBody>
      </Card>

      <Card className="mt-4">
        <CardTitle>Start an observation session</CardTitle>
        <CardBody>
          <p className="text-sm leading-relaxed text-ink-soft">
            Voice and text capture record the same observation data. Text
            input always works; voice needs microphone permission and a
            configured speech service.
          </p>
          {/* Button defaults to type="button" (never an accidental submit), so
              these two must opt into submit explicitly — otherwise the form's
              server action is never invoked and the click is a silent no-op. */}
          <div className="mt-4 flex flex-wrap items-center gap-3">
            <form action={startSession.bind(null, child.id, "voice")}>
              <Button type="submit" aria-label="Start a voice observation session">
                Start voice session
              </Button>
            </form>
            <form action={startSession.bind(null, child.id, "text")}>
              <Button
                type="submit"
                variant="secondary"
                aria-label="Start a text observation session"
              >
                Start text session
              </Button>
            </form>
          </div>
        </CardBody>
      </Card>

      {/* Roster membership. Archive, never delete: the record and every
          screening result behind it survive, because retention for a child's
          health data is a policy decision, not a button. */}
      <div className="mt-4">
        {child.archived_reason ? (
          <ArchiveChild
            childId={child.id}
            childName={child.name}
            archivedReason={child.archived_reason}
          />
        ) : null}
      </div>

      {/* FEAT-09: every displayed flag carries its visible, traceable basis
          (reasoning trail with knowledge-base descriptions + sources). */}
      <Card className="mt-4">
        <CardTitle>Screening history</CardTitle>
        <CardBody>
          {flags.length === 0 ? (
            <p className="text-sm text-ink-soft">
              No screening results recorded yet. Start a session above and
              ask SIGNAL about what you noticed.
            </p>
          ) : (
            <ul className="space-y-4">
              {flags.map((flag, index) => {
                const meta = gradeMeta(flag.confidence_grade);
                return (
                  <li key={flag.id} className="rounded-xl border border-line p-4">
                    <div className="flex flex-wrap items-center gap-2">
                      <Badge tone={gradeBadgeTone(flag.confidence_grade)}>
                        {meta ? `${meta.label} — ${meta.headline}` : flag.confidence_grade}
                      </Badge>
                      <Badge tone="neutral">
                        {domainLabel(flag.domain) ?? flag.domain}
                      </Badge>
                      <span className="ml-auto text-xs text-ink-soft">
                        {flag.created_at.slice(0, 10)}
                      </span>
                    </div>
                    {flag.explanation_text && (
                      <p className="mt-2 text-sm leading-relaxed text-ink">
                        {flag.explanation_text}
                      </p>
                    )}
                    {/* Same trail component the live conclusion renders, so a
                        result looks identical whether it is read now or six
                        months later during a review. */}
                    {/* The newest result opens with its basis showing: the
                        reviewable basis is the point of the record, not a
                        detail to be clicked for. Older ones stay collapsed. */}
                    <details className="group mt-3" open={index === 0}>
                      <summary className="cursor-pointer list-none text-xs font-bold tracking-[0.12em] text-pine uppercase hover:underline">
                        Why — the knowledge-base basis ({flag.reasoning_trail.length})
                        <span aria-hidden="true" className="ml-1 inline-block group-open:hidden">
                          ▸
                        </span>
                        <span aria-hidden="true" className="ml-1 hidden group-open:inline-block">
                          ▾
                        </span>
                      </summary>
                      <div className="mt-2">
                        <ReasoningTrail entries={flag.reasoning_trail} />
                      </div>
                    </details>
                  </li>
                );
              })}
            </ul>
          )}
        </CardBody>
      </Card>

      {/* Last, and quiet. Removing a child from the roster is a real action
          with a real reason behind it, but it is not what anyone came to this
          page to do. */}
      {!child.archived_reason && (
        <div className="mt-6 border-t border-line pt-5">
          <ArchiveChild
            childId={child.id}
            childName={child.name}
            archivedReason={null}
          />
          <p className="mt-2 max-w-prose text-xs leading-relaxed text-ink-soft">
            Archiving takes a child off the active roster — for a duplicate
            registration, or a child who has left. Nothing is deleted and it
            can be undone.
          </p>
        </div>
      )}
    </main>
  );
}
