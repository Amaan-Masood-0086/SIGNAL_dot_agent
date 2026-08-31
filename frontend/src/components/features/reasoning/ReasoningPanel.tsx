"use client";

import { useState } from "react";

import { Badge } from "@/src/components/ui/Badge";
import { Button } from "@/src/components/ui/Button";
import type { ReasoningResult } from "@/src/lib/api/schemas";

interface ReasoningPanelProps {
  sessionId: string;
  active: boolean;
}

interface Exchange {
  role: "caretaker" | "signal";
  text: string;
}

const GRADE_LABELS: Record<string, string> = {
  HIGH: "High — see a clinician soon",
  MODERATE: "Moderate — have it checked",
  LOW_MONITOR: "Low — monitor & recheck",
  INSUFFICIENT_INFORMATION: "Not enough information yet",
};

function gradeTone(grade: string | null): "danger" | "warning" | "neutral" {
  if (grade === "HIGH") return "danger";
  if (grade === "MODERATE") return "warning";
  return "neutral";
}

function domainLabel(domain: string | null): string | null {
  if (domain === "Speech_Language") return "Speech & language";
  if (domain === "Hearing") return "Hearing";
  return domain;
}

// FEAT-06 adaptive follow-up loop surface. The caretaker describes what they
// noticed; SIGNAL may ask up to 5 turns of discriminating follow-up
// questions before concluding. Every conclusion shows its grade, the
// domain it was filed under, and the knowledge-base basis (citation refs) —
// never a diagnosis (ADR-07).
export function ReasoningPanel({ sessionId, active }: ReasoningPanelProps) {
  const [exchanges, setExchanges] = useState<Exchange[]>([]);
  const [draft, setDraft] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ReasoningResult | null>(null);

  const concluded =
    result !== null && result.status !== "follow_up";

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
    } catch {
      setError("Reasoning failed");
    } finally {
      setPending(false);
    }
  }

  return (
    <section aria-label="Screening conversation" className="mt-10">
      <div className="flex flex-wrap items-center gap-3">
        <h2 className="font-display text-lg font-semibold text-ink">
          Ask SIGNAL about what you noticed
        </h2>
        {result?.status === "follow_up" && (
          <Badge tone="neutral">
            Question {result.turn} of up to {result.max_turns}
          </Badge>
        )}
      </div>
      <p className="mt-1 text-sm text-ink-soft">
        Describe what the child says or does. SIGNAL may ask a few follow-up
        questions (at most {result?.max_turns ?? 5}) before reaching a
        conclusion. This is a screening aid — it never diagnoses.
      </p>

      {exchanges.length > 0 && (
        <ol aria-label="Screening exchange" className="mt-4 space-y-3">
          {exchanges.map((exchange, index) => (
            <li
              key={index}
              className={
                exchange.role === "caretaker"
                  ? "ml-auto max-w-[85%] rounded-xl border border-line bg-moss/60 p-3"
                  : "mr-auto max-w-[85%] rounded-xl border border-line bg-surface p-3"
              }
            >
              <p className="text-xs font-semibold tracking-wide text-ink-soft uppercase">
                {exchange.role === "caretaker" ? "You" : "SIGNAL"}
              </p>
              <p className="mt-1 text-sm leading-relaxed whitespace-pre-wrap text-ink">
                {exchange.text}
              </p>
            </li>
          ))}
        </ol>
      )}

      {!concluded && active && (
        <div className="mt-4">
          <label htmlFor="reason-input" className="block text-sm font-medium text-ink-soft">
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
            className="mt-1 w-full rounded-xl border border-line bg-surface p-3 text-sm text-ink placeholder:text-ink-soft/60 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-pine"
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

      {concluded && result && (
        <div className="mt-5 rounded-xl border border-line bg-surface p-5">
          {result.status === "safeguarding_escalation" ? (
            <>
              <Badge tone="danger">Handled separately</Badge>
              <p className="mt-3 text-sm leading-relaxed text-ink">
                {result.explanation_text ??
                  "What you described is being handled through the safeguarding pathway, separately from developmental screening."}
              </p>
            </>
          ) : (
            <>
              <div className="flex flex-wrap items-center gap-2">
                <Badge tone={gradeTone(result.grade)}>
                  {result.grade ? GRADE_LABELS[result.grade] ?? result.grade : "Conclusion"}
                </Badge>
                {domainLabel(result.domain) && (
                  <Badge tone="neutral">{domainLabel(result.domain)}</Badge>
                )}
                {result.age_uncertain && (
                  <Badge tone="warning">Age is an estimate</Badge>
                )}
                {result.loop_exhausted && (
                  <Badge tone="neutral">Concluded at the turn limit</Badge>
                )}
              </div>
              {result.explanation_text && (
                <p className="mt-3 text-sm leading-relaxed text-ink">
                  {result.explanation_text}
                </p>
              )}
              {result.citations.length > 0 && (
                <div className="mt-4">
                  <p className="text-xs font-semibold tracking-wide text-ink-soft uppercase">
                    Basis in the knowledge base
                  </p>
                  <ul className="mt-1 flex flex-wrap gap-2">
                    {result.citations.map((ref) => (
                      <li
                        key={ref}
                        className="rounded-full border border-line bg-moss px-2.5 py-1 text-[11px] font-semibold text-pine-deep"
                      >
                        {ref}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {result.status === "insufficient_information" && (
                <p className="mt-3 text-xs text-ink-soft">
                  This is not a reassuring result — it means the check should
                  be repeated with someone who knows the child day to day.
                </p>
              )}
            </>
          )}
        </div>
      )}

      {error && (
        <p className="mt-4 rounded-lg bg-red-soft p-3 text-sm font-medium text-red" role="alert">
          {error}
        </p>
      )}
    </section>
  );
}
