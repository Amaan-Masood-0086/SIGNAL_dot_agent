"use client";

import Link from "next/link";
import { useRef, useState } from "react";

import { PageHeader } from "@/src/components/layout/PageHeader";
import { VoiceRecorder } from "@/src/components/features/voice-recorder/VoiceRecorder";
import { ReasoningPanel } from "@/src/components/features/reasoning/ReasoningPanel";
import { Alert } from "@/src/components/ui/Alert";
import { Badge } from "@/src/components/ui/Badge";
import { Button } from "@/src/components/ui/Button";
import { Icon } from "@/src/components/ui/Icon";
import type { Observation, Session } from "@/src/lib/api/schemas";

interface SessionChatProps {
  session: Session;
  childName: string | null;
  initialTurns: Observation[];
}

// FEAT-03 capture surface. Both modes converge on the same POST body
// ({ raw_input }) — voice first transcribes, then the caretaker reviews and
// saves the text, so the stored observation is identical either way. The
// text box is always visible: it is the fallback when STT is unconfigured
// (503) and works with zero STT dependency.
export function SessionChat({ session, childName, initialTurns }: SessionChatProps) {
  const [turns, setTurns] = useState<Observation[]>(initialTurns);
  const [status, setStatus] = useState<Session["status"]>(session.status);
  const [draft, setDraft] = useState("");
  const [pending, setPending] = useState(false);
  const [transcribing, setTranscribing] = useState(false);
  const [sttDown, setSttDown] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const active = status === "in_progress";
  const voiceMode = session.mode === "voice";

  async function submitTurn(rawInput: string) {
    setError(null);
    setPending(true);
    try {
      const response = await fetch(`/api/sessions/${session.id}/observations`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ raw_input: rawInput }),
      });
      const payload = (await response.json()) as
        | { observation: Observation }
        | { detail: string };
      if (!response.ok || !("observation" in payload)) {
        setError("detail" in payload ? payload.detail : "Request failed");
        if (response.status === 409) {
          setStatus("completed");
        }
        return;
      }
      setTurns((previous) => [...previous, payload.observation]);
      setDraft("");
    } catch {
      setError("Request failed");
    } finally {
      setPending(false);
    }
  }

  async function handleRecorded(audio: Blob) {
    setError(null);
    setTranscribing(true);
    try {
      const form = new FormData();
      form.append("audio", audio, "turn.webm");
      const response = await fetch("/api/stt/transcribe", {
        method: "POST",
        body: form,
      });
      const payload = (await response.json()) as
        | { transcript: { transcript: string; language: string } }
        | { detail: string };
      if (!response.ok || !("transcript" in payload)) {
        if (response.status === 503) {
          // STT not configured: degrade gracefully to the text box.
          setSttDown(true);
          setError(
            "detail" in payload
              ? payload.detail
              : "Voice input is unavailable; use the text box",
          );
        } else {
          setError("detail" in payload ? payload.detail : "Transcription failed");
        }
        return;
      }
      // Transcript lands in the text box for review/correction before it is
      // saved — the same submission path as typed input.
      setDraft(payload.transcript.transcript);
      textareaRef.current?.focus();
    } catch {
      setError("Transcription failed");
    } finally {
      setTranscribing(false);
    }
  }

  async function handleComplete() {
    setError(null);
    setPending(true);
    try {
      const response = await fetch(`/api/sessions/${session.id}/complete`, {
        method: "POST",
      });
      const payload = (await response.json()) as
        | { session: Session }
        | { detail: string };
      if (!response.ok || !("session" in payload)) {
        setError("detail" in payload ? payload.detail : "Request failed");
        return;
      }
      setStatus(payload.session.status);
    } catch {
      setError("Request failed");
    } finally {
      setPending(false);
    }
  }

  return (
    <main className="mx-auto w-full max-w-3xl p-5 sm:p-8">
      <Link
        href={`/dashboard/children/${session.child_id}`}
        className="inline-flex items-center gap-1 text-sm font-medium text-pine hover:underline"
      >
        ← {childName ? `Back to ${childName}` : "Back to the child profile"}
      </Link>

      <div className="mt-3">
        <PageHeader
          eyebrow={`Observation session · ${voiceMode ? "Voice mode" : "Text mode"}`}
          title={childName ?? "Session"}
          lede={
            voiceMode
              ? "Recorded speech becomes a transcript you review before it is saved. The audio itself is never stored."
              : "Typed observations are stored exactly as written — the same format voice mode produces."
          }
          actions={
            <Badge tone={active ? "neutral" : "success"}>
              {active ? "In progress" : "Completed"}
            </Badge>
          }
        />
      </div>

      {error && (
        <div className="mt-4">
          <Alert tone="danger">{error}</Alert>
        </div>
      )}

      {/* Part 1 — the record of what happened. Deliberately separated from
          the screening conversation below: the two used to sit as adjacent
          textareas with near-identical placeholders, so it was not visible
          which one stored an observation and which one asked for a grade. */}
      <section
        aria-label="Observation log"
        className="mt-6 rounded-xl border border-line bg-surface"
      >
        <header className="flex flex-wrap items-center gap-2 border-b border-line p-5">
          <div className="mr-auto">
            <h2 className="font-display text-lg font-semibold tracking-tight text-ink">
              Observation log
            </h2>
            <p className="mt-1 text-xs text-ink-soft">
              What the child said or did, recorded verbatim. Nothing here is
              graded — it is the record.
            </p>
          </div>
          <Badge tone="neutral">
            {turns.length} {turns.length === 1 ? "turn" : "turns"}
          </Badge>
        </header>

        <div className="p-5">
          {turns.length === 0 ? (
            <div className="rounded-xl border border-dashed border-line px-5 py-8 text-center">
              <span className="mx-auto flex h-10 w-10 items-center justify-center rounded-full bg-moss text-pine">
                <Icon name="children" className="h-5 w-5" />
              </span>
              <p className="mt-3 text-sm font-semibold text-ink">
                No turns recorded yet
              </p>
              <p className="mt-1 text-xs text-ink-soft">
                {voiceMode
                  ? "Record the first observation below, or type it."
                  : "Type the first observation below."}
              </p>
            </div>
          ) : (
            <ol className="space-y-3">
              {turns.map((turn) => (
                <li key={turn.id} className="flex gap-3">
                  <span
                    aria-hidden="true"
                    className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-moss font-display text-xs font-bold text-pine-deep"
                  >
                    {turn.turn_number}
                  </span>
                  <div className="min-w-0 flex-1 rounded-xl border border-line bg-moss/25 px-4 py-3">
                    <p className="text-sm leading-relaxed whitespace-pre-wrap text-ink">
                      {turn.raw_input}
                    </p>
                  </div>
                </li>
              ))}
            </ol>
          )}

          {active && (
            <div className="mt-5 border-t border-line pt-5">
              {voiceMode && !sttDown && (
                <div className="mb-4">
                  <VoiceRecorder
                    disabled={pending || transcribing}
                    onRecorded={handleRecorded}
                  />
                  {transcribing && (
                    <p
                      className="mt-2 text-xs font-medium text-pine"
                      role="status"
                      aria-live="polite"
                    >
                      Transcribing…
                    </p>
                  )}
                </div>
              )}
              <label
                htmlFor="turn-input"
                className="block text-sm font-medium text-ink"
              >
                {voiceMode && !sttDown
                  ? "Review the transcript, correct it if needed, or type here"
                  : "Record an observation"}
              </label>
              <textarea
                id="turn-input"
                ref={textareaRef}
                value={draft}
                onChange={(event) => setDraft(event.target.value)}
                rows={3}
                maxLength={10_000}
                className="mt-1.5 w-full rounded-xl border border-line bg-surface p-3 text-sm text-ink placeholder:text-ink-soft/60 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-pine"
                placeholder="What did the child say or do?"
                disabled={!active}
              />
              <div className="mt-3 flex flex-wrap items-center gap-2">
                <Button
                  onClick={() => void submitTurn(draft)}
                  disabled={pending || transcribing || draft.trim().length === 0}
                  aria-label="Save this turn"
                >
                  {pending ? "Saving…" : "Save turn"}
                </Button>
                <Button
                  variant="secondary"
                  onClick={() => void handleComplete()}
                  disabled={pending || transcribing}
                  aria-label="Complete this observation session"
                >
                  Complete session
                </Button>
              </div>
            </div>
          )}
        </div>
      </section>

      {/* Part 2 — FEAT-06: the adaptive screening loop, capped at max_turns
          server-side, concluding with a graded, cited result. */}
      <div className="mt-4">
        <ReasoningPanel sessionId={session.id} active={active} />
      </div>

      <div className="mt-6">
        <Link
          href="/dashboard"
          className="text-sm font-medium text-pine hover:underline"
        >
          ← All children
        </Link>
      </div>
    </main>
  );
}
