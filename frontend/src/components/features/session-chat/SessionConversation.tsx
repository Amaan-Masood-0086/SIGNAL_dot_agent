"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";

import { GradeVerdict } from "@/src/components/features/reasoning/GradeVerdict";
import { ReasoningTrail } from "@/src/components/features/reasoning/ReasoningTrail";
import { VoiceRecorder } from "@/src/components/features/voice-recorder/VoiceRecorder";
import { PageHeader } from "@/src/components/layout/PageHeader";
import { Alert } from "@/src/components/ui/Alert";
import { Badge } from "@/src/components/ui/Badge";
import { Button } from "@/src/components/ui/Button";
import { Icon } from "@/src/components/ui/Icon";
import { ThinkingBar } from "@/src/components/ui/ThinkingBar";
import type {
  FlagRead,
  Observation,
  ReasoningResult,
  Session,
  TrailEntryRead,
} from "@/src/lib/api/schemas";
import { domainLabel } from "@/src/lib/screening/grade";
import { useTranscription } from "@/src/lib/stt/useTranscription";

/**
 * One session, one conversation, one input.
 *
 * This replaces two stacked panels ("Observation log" + "Ask SIGNAL") that
 * each had their own consent box, microphone, textarea and buttons. Three
 * separate rounds of feedback said the same thing: nobody could tell which
 * box to use.
 *
 * The split was never justified by the data either. `reasoning.py` reads
 * EVERY observation in the session as the screening conversation's history,
 * and both boxes consumed the same five-turn budget — so underneath there
 * was always one list of turns, presented as two things. Now the shape of
 * the screen matches the shape of the data: one transcript, one place to
 * speak or type, and a choice about what this turn is for.
 */
const MAX_TURNS = 5;

interface Props {
  session: Session;
  childName: string | null;
  initialTurns: Observation[];
  savedFlags: FlagRead[];
  savedFlagTotal: number;
  initialResult: ReasoningResult | null;
}

function isSignalQuestion(turn: Observation): boolean {
  // The backend marks its own follow-up rows; they do not count against the
  // caretaker's turn budget and must not read as something a person said.
  const signals = turn.extracted_signals as { follow_up?: boolean } | null;
  return signals?.follow_up === true;
}

export function SessionConversation({ session, childName, initialTurns, savedFlags, savedFlagTotal, initialResult }: Props) {
  const [turns, setTurns] = useState<Observation[]>(initialTurns);
  const [status, setStatus] = useState<Session["status"]>(session.status);
  const [draft, setDraft] = useState("");
  const [pending, setPending] = useState<"ask" | "save" | "complete" | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ReasoningResult | null>(savedFlags.length ? null : initialResult);
  const requestRef = useRef<{ text: string; language: string; id: string } | null>(null);
  const [trail, setTrail] = useState<TrailEntryRead[] | null>(null);
  const draftRef = useRef<HTMLTextAreaElement>(null);
  const threadRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const node = threadRef.current;
    if (node) node.scrollTop = node.scrollHeight;
  }, [turns, pending]);

  /**
   * Which language SIGNAL replies in.
   *
   * "auto" mirrors what the caretaker wrote and is right most of the time.
   * It cannot be right always: typing Roman English because the keyboard is
   * easier, while reading Urdu far more comfortably, is common here and no
   * detection can see it. So the choice exists — once per device, not once
   * per turn, because a decision on every message is friction, not control.
   *
   * localStorage, wrapped: it is a display convenience, and a browser that
   * refuses storage must still render a working screen.
   */
  const [language, setLanguage] = useState<"auto" | "ur" | "en">("auto");
  useEffect(() => {
    // Read after hydration; server and first client render must agree.
    const task = window.setTimeout(() => {
      try {
        const saved = localStorage.getItem("signal.replyLanguage");
        if (saved === "ur" || saved === "en") setLanguage(saved);
      } catch { /* A blocked preference store does not block capture. */ }
    }, 0);
    return () => window.clearTimeout(task);
  }, []);

  useEffect(() => {
    if (!draft.trim()) return;
    const warn = (event: BeforeUnloadEvent) => { event.preventDefault(); };
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [draft]);

  function chooseLanguage(next: "auto" | "ur" | "en") {
    setLanguage(next);
    try {
      localStorage.setItem("signal.replyLanguage", next);
    } catch {
      // Preference simply will not persist; the session still works.
    }
  }

  const {
    transcribe,
    transcribing,
    unavailable: sttDown,
    error: sttError,
  } = useTranscription();

  const active = status === "in_progress";
  const voiceMode = session.mode === "voice";
  const concluded = savedFlags.length > 0 || (result !== null && result.status !== "follow_up");

  /**
   * The question SIGNAL is waiting on, if any.
   *
   * Read from the last turn rather than from `result`, so it survives a page
   * reload: the server records its own follow-up rows, and a caretaker who
   * comes back to a session must still see what was asked of them.
   */
  const lastTurn = turns.length > 0 ? turns[turns.length - 1] : null;
  const pendingQuestion =
    active && lastTurn && isSignalQuestion(lastTurn) && !concluded
      ? lastTurn.raw_input
      : null;

  // The budget the backend actually enforces: caretaker turns only.
  const turnsUsed = turns.filter((turn) => !isSignalQuestion(turn)).length;
  const turnsLeft = Math.max(0, MAX_TURNS - turnsUsed);
  const exhausted = turnsLeft === 0;

  async function handleRecorded(audio: Blob) {
    const transcript = await transcribe(audio);
    if (transcript === null) return;
    // Reviewed before it is used: what gets stored is what a person
    // approved, not what a model heard.
    setDraft(transcript);
    draftRef.current?.focus();
  }

  async function loadTrail(flagId: string) {
    try {
      const response = await fetch(`/api/flags/${flagId}`);
      if (!response.ok) return;
      const payload = (await response.json()) as { flag?: FlagRead };
      if (payload.flag) setTrail(payload.flag.reasoning_trail);
    } catch {
      // Degraded, not broken — the refs still render.
    }
  }

  /** Record the turn without grading it. No LLM call, no cost. */
  async function saveOnly() {
    const text = draft.trim();
    if (!text || pending) return;
    setPending("save");
    setError(null);
    try {
      const response = await fetch(`/api/sessions/${session.id}/observations`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ raw_input: text }),
      });
      const payload = (await response.json()) as
        | { observation: Observation }
        | { detail: string };
      if (!response.ok || !("observation" in payload)) {
        setError("detail" in payload ? payload.detail : "The turn could not be saved.");
        return;
      }
      setTurns((previous) => [...previous, payload.observation]);
      setDraft("");
    } catch {
      setError("The turn could not be saved.");
    } finally {
      setPending(null);
    }
  }

  /** Record the turn AND screen it. */
  async function ask() {
    const text = draft.trim();
    if (!text || pending) return;
    setPending("ask");
    setError(null);
    if (requestRef.current?.text !== text || requestRef.current.language !== language) {
      requestRef.current = { text, language, id: crypto.randomUUID() };
    }
    try {
      const response = await fetch(`/api/sessions/${session.id}/reason`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ raw_input: text, response_language: language, request_id: requestRef.current.id }),
      });
      const payload = (await response.json()) as
        | { result: ReasoningResult }
        | { detail: string };
      if (!response.ok || !("result" in payload)) {
        setError("detail" in payload ? payload.detail : "SIGNAL could not answer.");
        return;
      }
      const next = payload.result;
      requestRef.current = null;
      setResult(next);
      setDraft("");
      if (next.flag_id) await loadTrail(next.flag_id);
      // Re-read the turns so the caretaker's turn and SIGNAL's question both
      // appear from the server's own record rather than a local guess.
      const fresh = await fetch(
        `/api/sessions/${session.id}/observations?page=1&page_size=100`,
      );
      if (fresh.ok) {
        const body = (await fresh.json()) as { result?: { items: Observation[] } };
        if (body.result) setTurns(body.result.items);
      }
    } catch {
      setError("SIGNAL could not answer.");
    } finally {
      setPending(null);
    }
  }

  async function complete() {
    setPending("complete");
    setError(null);
    try {
      const response = await fetch(`/api/sessions/${session.id}/complete`, {
        method: "POST",
      });
      const payload = (await response.json()) as
        | { session: Session }
        | { detail: string };
      if (!response.ok || !("session" in payload)) {
        setError("detail" in payload ? payload.detail : "The session could not be closed.");
        return;
      }
      setStatus(payload.session.status);
    } catch {
      setError("The session could not be closed.");
    } finally {
      setPending(null);
    }
  }

  const busy = pending !== null || transcribing;
  const empty = draft.trim().length === 0;

  return (
    <main className="screening-workspace mx-auto w-full max-w-6xl p-5 sm:p-8">
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
              ? "Speak or type what you noticed. Review your words before sending them."
              : "Describe what you noticed, then answer any follow-up questions."
          }
          actions={
            <Badge tone={active ? "neutral" : "success"}>
              {active ? "In progress" : status === "abandoned" ? "Abandoned" : "Completed"}
            </Badge>
          }
        />
      </div>

      {(error ?? sttError) && (
        <div className="mt-4">
          <Alert tone="danger">{error ?? sttError}</Alert>
        </div>
      )}

      <div className="chat-layout">
      <div>
      {savedFlags.length > 0 && (
        <section aria-label="Saved screening results" className="mb-6 space-y-4">
          <h2 className="font-display text-xl font-semibold">Saved screening results</h2>
          <p className="text-sm text-ink-soft">Previously recorded results, restored without running another screening. This is screening guidance, not a diagnosis.</p>
          {savedFlagTotal > savedFlags.length && <p className="text-sm text-ink-soft">Showing the latest {savedFlags.length} of {savedFlagTotal} results.</p>}
          {savedFlags.map(flag => (
            <article key={flag.id} className="space-y-3">
              <Link href={`/dashboard/referrals/new?flag=${flag.id}`} className="inline-flex text-sm font-semibold text-pine">Referral &amp; follow-up</Link>
              <GradeVerdict grade={flag.confidence_grade}>
                <p className="mt-3 text-sm">{domainLabel(flag.domain) ?? flag.domain}</p>
                <time className="mt-1 block text-xs text-ink-soft" dateTime={flag.created_at}>{flag.created_at.replace("T", " ")}</time>
              </GradeVerdict>
              {flag.explanation_text && <p dir="auto" className="record-text whitespace-pre-wrap text-sm">{flag.explanation_text}</p>}
              {flag.reasoning_trail.length > 0 ? <ReasoningTrail entries={flag.reasoning_trail} /> : <p className="text-sm text-ink-soft">No evidence entries were returned with this saved result.</p>}
            </article>
          ))}
        </section>
      )}
      <section
        aria-label="Session conversation"
        className="screening-chat"
      >
        <header className="flex flex-wrap items-center gap-2 border-b border-line p-5">
          <div className="mr-auto">
            <h2 className="font-display text-lg font-semibold tracking-tight text-ink">
              Chat with SIGNAL
            </h2>
              <p className="mt-1 max-w-prose text-xs leading-relaxed text-ink-soft">
                Share what you noticed. SIGNAL will ask one focused question at a time.
              </p>
          </div>
          {/* The budget the backend enforces, shown before it runs out
              instead of surfacing as a sudden refusal at the sixth turn. */}
          <Badge tone={turnsLeft <= 1 ? "warning" : "neutral"}>
            {concluded ? "Result saved" : `${turnsUsed} / ${MAX_TURNS} messages used`}
          </Badge>
        </header>

        <div className="chat-body">
        <div className="chat-thread" ref={threadRef} role="log" aria-label="Conversation messages" aria-live="polite">
          {turns.length === 0 ? (
            <div className="chat-welcome">
              <span className="brand-mark">
                <Icon name="children" className="h-5 w-5" />
              </span>
              <p className="chat-sender">SIGNAL · Observation assistant</p>
              <h3>What have you noticed about {childName || "the child"}?</h3>
              <p>Tell me what you have seen or heard, and when it happens. I may ask a follow-up to understand it better.</p>
              <p className="chat-welcome-note">It is okay to say “I don’t know”. You do not need to guess.</p>
              <p className="mt-1 text-xs text-ink-soft">
                {voiceMode
                  ? "Speak or type the first turn below."
                  : "Write naturally—there is no form to complete."}
              </p>
            </div>
          ) : (
            <ol className="space-y-3">
              {turns.map((turn) => {
                const fromSignal = isSignalQuestion(turn);
                return (
                  <li
                    key={turn.id}
                    className={
                      fromSignal
                        ? "chat-message chat-message-signal"
                        : "chat-message chat-message-user"
                    }
                  >
                    <p className="flex items-center gap-1.5 text-xs font-bold tracking-[0.12em] text-ink-soft uppercase">
                      {fromSignal && (
                        <Icon name="shield" className="h-3.5 w-3.5 text-pine" />
                      )}
                      {fromSignal ? "SIGNAL asks" : "You"}
                    </p>
                    <p dir="auto" className="record-text mt-1 text-sm leading-relaxed whitespace-pre-wrap text-ink">
                      {turn.raw_input}
                    </p>
                  </li>
                );
              })}
            </ol>
          )}
          {pending === "ask" && <div className="chat-message chat-message-signal" role="status"><p className="chat-sender">SIGNAL</p><ThinkingBar /></div>}
        </div>

          {active && !concluded && (
            <div className="chat-composer">
              {voiceMode && !sttDown && (
                <div className="mb-4">
                  <VoiceRecorder disabled={busy} onRecorded={handleRecorded} />
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

              {/* A pending question is restated HERE, next to the box, not
                  only up in the transcript. Merging the two panels dropped
                  the "answer this" state the old screening panel had, and a
                  real session then burned all five turns on "now tell me"
                  because nothing said a question was waiting. The whole
                  screening depends on that answer arriving. */}
              {pendingQuestion && (
                <div className="mb-3 rounded-xl border border-pine/30 bg-moss/50 p-4">
                  <p className="flex items-center gap-1.5 text-xs font-bold tracking-[0.12em] text-pine-deep uppercase">
                    <Icon name="shield" className="h-3.5 w-3.5 text-pine" />
                    SIGNAL is waiting for this answer
                  </p>
                  <p className="mt-1.5 text-sm leading-relaxed text-ink">
                    {pendingQuestion}
                  </p>
                  <p className="mt-2 text-xs leading-relaxed text-ink-soft">
                    Without it there is nothing to grade — the result comes back
                    as &ldquo;not enough information&rdquo;.
                  </p>
                </div>
              )}

              <label htmlFor="turn-input" className="block text-sm font-medium text-ink">
                {pendingQuestion
                  ? voiceMode && !sttDown
                    ? "Speak or type your answer, then review it"
                    : "Your answer"
                  : voiceMode && !sttDown
                    ? "Speak or type this turn, then review it"
                    : "What did you notice?"}
              </label>
              <textarea
                dir="auto"
                id="turn-input"
                ref={draftRef}
                value={draft}
                onChange={(event) => setDraft(event.target.value)}
                rows={2}
                maxLength={10_000}
                disabled={busy || exhausted}
                onKeyDown={(event) => {
                  if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing && !busy && !exhausted) {
                    event.preventDefault();
                    void ask();
                  }
                }}
                placeholder={
                  pendingQuestion
                    ? "Answer the question above"
                    : "e.g. He doesn't turn around when I clap behind him"
                }
                className="mt-1.5 w-full rounded-xl border border-line bg-surface p-3 text-sm text-ink placeholder:text-ink-soft/60 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-pine"
              />

              {/* One input, two intents — weighted, because asking is what a
                  worried caretaker came to do. */}
              <div className="chat-actions">
              <Button
                  onClick={() => void ask()}
                  disabled={busy || empty || exhausted}
                  aria-label={pendingQuestion ? "Send answer to SIGNAL" : "Send observation to SIGNAL"}
                >
                  {pending === "ask" ? "Thinking…" : pendingQuestion ? "Send answer" : "Ask SIGNAL"}
                </Button>
                <Button
                  variant="ghost"
                  onClick={() => void saveOnly()}
                  disabled={busy || empty || exhausted || !!pendingQuestion}
                  aria-label="Save this turn without screening it"
                >
                  {pending === "save" ? "Saving…" : "Just save it"}
                </Button>
                <Button
                  variant="ghost"
                  onClick={() => void complete()}
                  disabled={busy || !empty}
                  className="ml-auto"
                  aria-label="Complete this observation session"
                >
                  Complete session
                </Button>
              </div>
              {/* Sits with the input, not in a settings page: it changes what
                  comes back from the very next Ask. Three choices, no free
                  text — the caretaker's own words stay fenced as data, so a
                  preference has to arrive as a structured field rather than
                  an instruction typed into the box. */}
              <div className="chat-language flex flex-wrap items-center gap-2">
                <span className="text-xs font-medium text-ink-soft">
                  SIGNAL replies in
                </span>
                <div role="group" aria-label="Reply language" className="flex gap-1.5">
                  {(
                    [
                      { id: "auto" as const, label: "Same as I write" },
                      { id: "ur" as const, label: "اردو" },
                      { id: "en" as const, label: "English" },
                    ]
                  ).map((option) => (
                    <button
                      key={option.id}
                      type="button"
                      onClick={() => chooseLanguage(option.id)}
                      aria-pressed={language === option.id}
                      className={`min-h-9 rounded-full border px-3 py-1.5 text-xs font-semibold transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-pine ${
                        language === option.id
                          ? "border-pine bg-pine text-white"
                          : "border-line bg-surface text-ink-soft hover:border-pine/40 hover:text-ink"
                      }`}
                    >
                      {option.label}
                    </button>
                  ))}
                </div>
                <span className="text-xs text-ink-soft">
                  Remembered on this device.
                </span>
              </div>


              <p className="mt-2 text-xs leading-relaxed text-ink-soft">
                {!empty ? "Your draft is not saved yet. Send or save it before completing the session." : "Ask SIGNAL saves and screens your observation. Just save it records without screening. Both use one turn."}
              </p>
              {exhausted && (
                <div className="mt-3">
                  <Alert tone="warning">
                    All {MAX_TURNS} turns are used, so this session has to
                    conclude. Complete it and start a new one if there is more to
                    record.
                  </Alert>
                </div>
              )}
            </div>
          )}

          {!active && !concluded && (
            <p className="mt-5 border-t border-line pt-5 text-sm text-ink-soft">
              This session is complete. Screening results stay on the child&rsquo;s
              profile.
            </p>
          )}
        </div>
      </section>

      {concluded && result && (
        <div className="mt-4 space-y-4">
          {result.status === "safeguarding_escalation" ? (
            <div className="overflow-hidden rounded-xl border border-red/30 bg-red-soft">
              <div aria-hidden="true" className="h-1 w-full bg-red" />
              <div className="p-5">
                <p className="text-xs font-bold tracking-[0.14em] text-red uppercase">
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
                <p className="text-sm leading-relaxed whitespace-pre-wrap text-ink">
                  {result.explanation_text}
                </p>
              )}

              {result.flag_id && <Link href={`/dashboard/referrals/new?flag=${result.flag_id}`} className="inline-flex text-sm font-semibold text-pine">Referral &amp; follow-up</Link>}

              {(trail !== null || result.citations.length > 0) && (
                <div className="rounded-xl border border-line bg-surface p-4">
                  <p className="text-xs font-bold tracking-[0.12em] text-ink-soft uppercase">
                    Why — the knowledge-base basis
                  </p>
                  <p className="mt-1 mb-3 text-xs text-ink-soft">
                    Every entry below is a row from the screening knowledge base.
                    Nothing here is generated free-hand.
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

      </div>
      <details className="chat-help">
        <summary>Writing an observation · Help and guidance</summary>
        <h2>A useful observation</h2>
        <ul className="mt-4"><li>Describe something you have personally seen or heard.</li><li>Include when it happens and whether it has changed.</li><li>If you do not know an answer, say so. You do not need to guess.</li></ul>
        <div className="mt-5 border-t border-line pt-5"><h2>What happens next?</h2><p className="mt-2">SIGNAL may ask a follow-up question. Any saved screening result and its evidence remain on the child’s profile.</p></div>
        <Link href="/dashboard/guide" className="mt-5 inline-flex text-xs font-semibold text-pine">Read the screening guide →</Link>
      </details>
      </div>

      <div className="mt-6">
        <Link href="/dashboard" className="text-sm font-medium text-pine hover:underline">
          ← All children
        </Link>
      </div>
    </main>
  );
}
