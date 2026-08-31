"use client";

import Link from "next/link";
import { useRef, useState } from "react";

import { VoiceRecorder } from "@/src/components/features/voice-recorder/VoiceRecorder";
import { ReasoningPanel } from "@/src/components/features/reasoning/ReasoningPanel";
import { Badge } from "@/src/components/ui/Badge";
import { Button } from "@/src/components/ui/Button";
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
    <main className="mx-auto w-full max-w-3xl p-6 sm:p-8">
      <div className="flex flex-wrap items-center gap-3">
        <div className="mr-auto">
          <p className="text-xs font-semibold tracking-[0.14em] text-ink-soft uppercase">
            Observation session · {session.mode === "voice" ? "Voice mode" : "Text mode"}
          </p>
          <h1 className="mt-1 font-display text-3xl font-bold tracking-tight text-ink">
            {childName ?? "Session"}
          </h1>
        </div>
        <Badge tone={active ? "neutral" : "success"}>
          {active ? "In progress" : "Completed"}
        </Badge>
      </div>

      <section aria-label="Recorded turns" className="mt-6">
        {turns.length === 0 ? (
          <div className="rounded-xl border border-dashed border-line bg-surface p-6">
            <p className="text-sm text-ink-soft">
              No turns recorded yet. Record or type the first observation
              below.
            </p>
          </div>
        ) : (
          <ol className="space-y-4">
            {turns.map((turn) => (
              <li key={turn.id} className="flex gap-3">
                <span
                  aria-hidden="true"
                  className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-line bg-surface font-display text-sm font-semibold text-pine"
                >
                  {turn.turn_number}
                </span>
                <div className="flex-1 rounded-xl border border-line bg-surface p-4">
                  <p className="text-xs font-semibold tracking-wide text-ink-soft uppercase">
                    Turn {turn.turn_number}
                  </p>
                  <p className="mt-1 text-sm leading-relaxed whitespace-pre-wrap text-ink">
                    {turn.raw_input}
                  </p>
                </div>
              </li>
            ))}
          </ol>
        )}
      </section>

      {active && (
        <section aria-label="Add a turn" className="mt-8">
          <h2 className="font-display text-lg font-semibold text-ink">
            Add a turn
          </h2>
          {session.mode === "voice" && !sttDown && (
            <div className="mt-3">
              <VoiceRecorder disabled={pending || transcribing} onRecorded={handleRecorded} />
              {transcribing && (
                <p className="mt-2 text-xs text-ink-soft" role="status" aria-live="polite">
                  Transcribing…
                </p>
              )}
            </div>
          )}
          <label htmlFor="turn-input" className="mt-4 block text-sm font-medium text-ink-soft">
            {session.mode === "voice" && !sttDown
              ? "Review the transcript, correct it if needed, or type here"
              : "Type the observation"}
          </label>
          <textarea
            id="turn-input"
            ref={textareaRef}
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            rows={4}
            maxLength={10_000}
            className="mt-1 w-full rounded-xl border border-line bg-surface p-3 text-sm text-ink placeholder:text-ink-soft/60 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-pine"
            placeholder="What did the child say or do?"
            disabled={!active}
          />
          <div className="mt-3 flex flex-wrap items-center gap-3">
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
        </section>
      )}

      {error && (
        <p className="mt-4 rounded-lg bg-red-soft p-3 text-sm font-medium text-red" role="alert">
          {error}
        </p>
      )}

      {/* FEAT-06: the adaptive screening loop — follow-up questions, capped
          at max_turns server-side, graded conclusion with cited basis. */}
      <ReasoningPanel sessionId={session.id} active={active} />

      <div className="mt-8">
        <Link
          href="/dashboard"
          className="text-sm font-medium text-pine hover:underline"
        >
          ← Back to dashboard
        </Link>
      </div>
    </main>
  );
}
