"use client";

import { useState } from "react";

import { GradeVerdict } from "@/src/components/features/reasoning/GradeVerdict";
import { ReasoningTrail } from "@/src/components/features/reasoning/ReasoningTrail";
import { Alert } from "@/src/components/ui/Alert";
import { Badge } from "@/src/components/ui/Badge";
import { Button } from "@/src/components/ui/Button";
import { Icon } from "@/src/components/ui/Icon";
import type { FlagRead, ReasoningResult, TrailEntryRead } from "@/src/lib/api/schemas";
import { domainLabel } from "@/src/lib/screening/grade";

interface ReasoningPanelProps {
  sessionId: string;
  active: boolean;
}

interface Exchange {
  role: "caretaker" | "signal";
  text: string;
}

// FEAT-06 adaptive follow-up loop surface. The caretaker describes what they
// noticed; SIGNAL may ask up to 5 turns of discriminating follow-up
// questions before concluding. Every conclusion shows its grade, the domain
// it was filed under, and the knowledge-base basis in full — never a
// diagnosis (ADR-07).
export function ReasoningPanel({ sessionId, active }: ReasoningPanelProps) {
  const [exchanges, setExchanges] = useState<Exchange[]>([]);
  const [draft, setDraft] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ReasoningResult | null>(null);
  const [trail, setTrail] = useState<TrailEntryRead[] | null>(null);

  const concluded = result !== null && result.status !== "follow_up";

  /** The reasoning response carries bare citation refs; the flag carries the
   *  resolved knowledge-base rows. Read the flag so the live conclusion shows
   *  the same reviewable basis the screening history shows. A failure here
   *  is not surfaced as an error — the refs still render (ReasoningTrail's
   *  `refsOnly` path) and the result itself is already saved. */
  async function loadTrail(flagId: string) {
    try {
      const response = await fetch(`/api/flags/${flagId}`);
      if (!response.ok) return;
      const payload = (await response.json()) as { flag?: FlagRead };
      if (payload.flag) setTrail(payload.flag.reasoning_trail);
    } catch {
      // Degraded, not broken: keep the refs-only view.
    }
  }

  async function submit() {
    const text = draft.trim();
    if (!text || pending) return;
    setError(null);
    setPending(true);
    try {
      const response = await fetch(`/api/sessions/${sessionId}/reason`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ raw_input: text }),
      });
      const payload = (await response.json()) as
        | { result: ReasoningResult }
        | { detail: string };
      if (!response.ok || !("result" in payload)) {
        setError("detail" in payload ? payload.detail : "Reasoning failed");
        return;
      }
      const next = payload.result;
      setExchanges((previous) => [
        ...previous,
        { role: "caretaker", text },
        ...(next.status === "follow_up" && next.follow_up_question
          ? [{ role: "signal" as const, text: next.follow_up_question }]
          : []),
      ]);
      setDraft("");
      setResult(next);
      if (next.flag_id) {
        await loadTrail(next.flag_id);
      }
    } catch {
      setError("Reasoning failed");
    } finally {
      setPending(false);
    }
  }

  const turnsUsed = result?.turn ?? 0;
  const maxTurns = result?.max_turns ?? 5;

  return (
    <section
      aria-label="Screening conversation"
      className="rounded-xl border border-line bg-surface"
    >
      <header className="border-b border-line p-5">
        <div className="flex flex-wrap items-center gap-2">
          <h2 className="mr-auto font-display text-lg font-semibold tracking-tight text-ink">
            Ask SIGNAL
          </h2>
          {result?.status === "follow_up" && (
            <Badge tone="neutral">
              Question {turnsUsed} of up to {maxTurns}
            </Badge>
          )}
          {concluded && <Badge tone="success">Concluded</Badge>}
        </div>
        <p className="mt-1.5 max-w-prose text-xs leading-relaxed text-ink-soft">
          Separate from the observation log above: this is the screening
          conversation. Describe a concern and SIGNAL may ask up to {maxTurns}{" "}
          follow-up questions before grading it against the knowledge base. It
          is a screening aid and never diagnoses.
        </p>
      </header>

      <div className="p-5">
        {exchanges.length > 0 && (
          <ol aria-label="Screening exchange" className="mb-5 space-y-3">
            {exchanges.map((exchange, index) => (
              <li
                key={index}
                className={
                  exchange.role === "caretaker"
                    ? "ml-auto max-w-[85%] rounded-xl rounded-br-sm border border-line bg-moss/60 px-4 py-3"
                    : "mr-auto max-w-[85%] rounded-xl rounded-bl-sm border border-line bg-surface px-4 py-3"
                }
              >
                <p className="flex items-center gap-1.5 text-[10px] font-bold tracking-[0.12em] text-ink-soft uppercase">
                  {exchange.role === "signal" && (
                    <Icon name="shield" className="h-3.5 w-3.5 text-pine" />
                  )}
                  {exchange.role === "caretaker" ? "You" : "SIGNAL asks"}
                </p>
                <p className="mt-1 text-sm leading-relaxed whitespace-pre-wrap text-ink">
                  {exchange.text}
                </p>
              </li>
            ))}
          </ol>
        )}

        {!concluded && active && (
          <div>
            <label
              htmlFor="reason-input"
              className="block text-sm font-medium text-ink"
            >
              {result?.status === "follow_up"
                ? "Answer SIGNAL's question"
                : "What have you noticed?"}
            </label>
            <textarea
              id="reason-input"
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              rows={3}
              maxLength={10_000}
              className="mt-1.5 w-full rounded-xl border border-line bg-surface p-3 text-sm text-ink placeholder:text-ink-soft/60 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-pine"
              placeholder="e.g. He doesn't turn around when I clap behind him"
            />
            <div className="mt-3">
              <Button
                onClick={() => void submit()}
                disabled={pending || draft.trim().length === 0}
                aria-label="Send to SIGNAL"
              >
                {pending
                  ? "Thinking…"
                  : result?.status === "follow_up"
                    ? "Answer"
                    : "Ask SIGNAL"}
              </Button>
            </div>
          </div>
        )}

        {!active && !concluded && exchanges.length === 0 && (
          <p className="text-sm text-ink-soft">
            This session is complete. Screening results stay on the child’s
            profile.
          </p>
        )}

        {concluded && result && (
          <div className="space-y-4">
            {result.status === "safeguarding_escalation" ? (
              // Deliberately no grade and no citations: a safeguarding
              // disclosure leaves the developmental-screening pathway
              // entirely rather than being graded as a milestone concern.
              <div className="overflow-hidden rounded-xl border border-red/30 bg-red-soft">
                <div aria-hidden="true" className="h-1 w-full bg-red" />
                <div className="p-5">
                  <p className="text-[11px] font-bold tracking-[0.14em] text-red uppercase">
                    Handled separately
                  </p>
                  <p className="mt-1.5 font-display text-2xl leading-tight font-bold tracking-tight text-ink">
                    Routed to the safeguarding pathway
                  </p>
                  <p className="mt-2 max-w-prose text-sm leading-relaxed text-ink-soft">
                    {result.explanation_text ??
                      "What you described is being handled through the safeguarding pathway, separately from developmental screening."}
                  </p>
                </div>
              </div>
            ) : (
              <>
                <GradeVerdict grade={result.grade}>
                  <div className="mt-4 flex flex-wrap items-center gap-2">
                    {domainLabel(result.domain) && (
                      <Badge tone="neutral">{domainLabel(result.domain)}</Badge>
                    )}
                    {result.age_uncertain && (
                      <Badge tone="warning">Grade downgraded — age is an estimate</Badge>
                    )}
                    {result.loop_exhausted && (
                      <Badge tone="neutral">Concluded at the question limit</Badge>
                    )}
                  </div>
                </GradeVerdict>

                {result.explanation_text && (
                  <p className="text-sm leading-relaxed text-ink">
                    {result.explanation_text}
                  </p>
                )}

                {(trail !== null || result.citations.length > 0) && (
                  <div className="rounded-xl border border-line bg-surface p-4">
                    <p className="text-[11px] font-bold tracking-[0.12em] text-ink-soft uppercase">
                      Why — the knowledge-base basis
                    </p>
                    <p className="mt-1 mb-3 text-xs text-ink-soft">
                      Every entry below is a row from the screening knowledge
                      base. Nothing here is generated free-hand.
                    </p>
                    <ReasoningTrail
                      entries={trail ?? undefined}
                      refsOnly={trail ? undefined : result.citations}
                    />
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {error && (
          <div className="mt-4">
            <Alert tone="danger">{error}</Alert>
          </div>
        )}
      </div>
    </section>
  );
}
