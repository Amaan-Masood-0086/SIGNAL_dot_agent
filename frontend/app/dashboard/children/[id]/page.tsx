import Link from "next/link";
import { notFound, redirect } from "next/navigation";

import { PageHeader } from "@/src/components/layout/PageHeader";
import { Badge } from "@/src/components/ui/Badge";
import { Button } from "@/src/components/ui/Button";
import { Card, CardBody, CardTitle } from "@/src/components/ui/Card";
import { getChild, isAuthorizationError } from "@/src/lib/api/children";
import { listChildFlags } from "@/src/lib/api/flags";
import type { FlagRead } from "@/src/lib/api/schemas";
import { createSession } from "@/src/lib/api/sessions";
import { getSessionToken } from "@/src/lib/auth/session";

const GRADE_LABELS: Record<string, string> = {
  high: "High — see a clinician soon",
  moderate: "Moderate — have it checked",
  low_monitor: "Low — monitor & recheck",
  insufficient_information: "Not enough information yet",
};

function gradeTone(grade: string): "danger" | "warning" | "neutral" | "success" {
  if (grade === "high") return "danger";
  if (grade === "moderate") return "warning";
  return "neutral";
}

function domainLabel(domain: string): string {
  return domain === "Speech_Language" ? "Speech & language" : domain;
}

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
          <div className="mt-4 flex flex-wrap items-center gap-3">
            <form action={startSession.bind(null, child.id, "voice")}>
              <Button aria-label="Start a voice observation session">
                Start voice session
              </Button>
            </form>
            <form action={startSession.bind(null, child.id, "text")}>
              <Button
                variant="secondary"
                aria-label="Start a text observation session"
              >
                Start text session
              </Button>
            </form>
          </div>
        </CardBody>
      </Card>

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
              {flags.map((flag) => (
                <li key={flag.id} className="rounded-xl border border-line p-4">
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge tone={gradeTone(flag.confidence_grade)}>
                      {GRADE_LABELS[flag.confidence_grade] ?? flag.confidence_grade}
                    </Badge>
                    <Badge tone="neutral">{domainLabel(flag.domain)}</Badge>
                    <span className="ml-auto text-xs text-ink-soft">
                      {flag.created_at.slice(0, 10)}
                    </span>
                  </div>
                  {flag.explanation_text && (
                    <p className="mt-2 text-sm leading-relaxed text-ink">
                      {flag.explanation_text}
                    </p>
                  )}
                  <details className="mt-3">
                    <summary className="cursor-pointer text-xs font-semibold tracking-wide text-pine uppercase">
                      Why — the cited basis ({flag.reasoning_trail.length})
                    </summary>
                    <ul className="mt-2 space-y-2">
                      {flag.reasoning_trail.map((entry) => (
                        <li
                          key={entry.citation_ref}
                          className="rounded-lg bg-moss/60 p-3 text-xs leading-relaxed text-ink"
                        >
                          <span className="font-semibold text-pine-deep">
                            {entry.citation_ref}
                          </span>{" "}
                          — {entry.description ?? entry.basis ?? "cited basis"}
                          {entry.source && (
                            <span className="text-ink-soft"> · {entry.source}</span>
                          )}
                        </li>
                      ))}
                    </ul>
                  </details>
                </li>
              ))}
            </ul>
          )}
        </CardBody>
      </Card>
    </main>
  );
}
