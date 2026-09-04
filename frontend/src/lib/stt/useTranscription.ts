"use client";

import { useState } from "react";

/**
 * Shared voice→text step for every surface that accepts a spoken turn.
 *
 * Extracted because the screening conversation needed the same capability the
 * observation log already had, and a second copy of this flow would have
 * drifted — the 503 fallback in particular is the part that must not diverge:
 * an unconfigured speech provider has to degrade to typing, never block the
 * turn (FEAT-03 acceptance).
 *
 * The transcript is returned rather than submitted. Every caller puts it in a
 * textarea for the caretaker to read and correct first, so what gets stored is
 * what a human approved — not what a model heard.
 */
export function useTranscription() {
  const [transcribing, setTranscribing] = useState(false);
  const [unavailable, setUnavailable] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function transcribe(audio: Blob): Promise<string | null> {
    setError(null);
    setTranscribing(true);
    try {
      const form = new FormData();
      form.append("audio", audio, "turn.webm");
      const response = await fetch("/api/stt/transcribe", { method: "POST", body: form });
      const payload = (await response.json()) as
        | { transcript: { transcript: string; language: string } }
        | { detail: string };

      if (!response.ok || !("transcript" in payload)) {
        if (response.status === 503) {
          // Speech provider not configured. Hide the microphone and fall back
          // to typing — the recorded observation is identical either way.
          setUnavailable(true);
          setError(
            "detail" in payload
              ? payload.detail
              : "Voice input is unavailable; type instead",
          );
        } else {
          setError("detail" in payload ? payload.detail : "Transcription failed");
        }
        return null;
      }
      return payload.transcript.transcript;
    } catch {
      setError("Transcription failed");
      return null;
    } finally {
      setTranscribing(false);
    }
  }

  return { transcribe, transcribing, unavailable, error, clearError: () => setError(null) };
}
