"use client";

import { useEffect, useRef, useState } from "react";

import { Button } from "@/src/components/ui/Button";

type RecorderState = "idle" | "recording";

// Per-turn duration cap: clips auto-stop at this many seconds. The backend
// separately enforces a 1.5 MB size guard (413) before anything reaches the
// STT provider — duration here, size there, both before the paid API call.
const MAX_TURN_SECONDS = 60;

interface VoiceRecorderProps {
  disabled?: boolean;
  onRecorded: (audio: Blob) => void;
}

// FEAT-03 voice capture (web-development.md Voice/Mic MUSTs): explicit
// visible consent before the microphone opens, a visible recording
// indicator, the stream is released after every turn, and every control
// carries an aria-label.
export function VoiceRecorder({ disabled, onRecorded }: VoiceRecorderProps) {
  const [consented, setConsented] = useState(false);
  const [state, setState] = useState<RecorderState>("idle");
  const [secondsLeft, setSecondsLeft] = useState(MAX_TURN_SECONDS);
  const [micError, setMicError] = useState<string | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const countdownRef = useRef<ReturnType<typeof setInterval> | null>(null);

  function clearCountdown() {
    if (countdownRef.current !== null) {
      clearInterval(countdownRef.current);
      countdownRef.current = null;
    }
  }

  // Safety net: never leak the microphone stream or timer past unmount.
  useEffect(() => {
    return () => {
      clearCountdown();
      streamRef.current?.getTracks().forEach((track) => track.stop());
    };
  }, []);

  async function startRecording() {
    setMicError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      const mimeType = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
        ? "audio/webm;codecs=opus"
        : undefined;
      const recorder = new MediaRecorder(
        stream,
        mimeType ? { mimeType } : undefined,
      );
      chunksRef.current = [];
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };
      recorder.onstop = () => {
        // Release the microphone immediately after each turn.
        stream.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
        const blob = new Blob(chunksRef.current, {
          type: mimeType ?? "audio/webm",
        });
        chunksRef.current = [];
        setState("idle");
        if (blob.size > 0) {
          onRecorded(blob);
        }
      };
      recorder.start();
      recorderRef.current = recorder;
      setState("recording");
      setSecondsLeft(MAX_TURN_SECONDS);
      countdownRef.current = setInterval(() => {
        setSecondsLeft((previous) => {
          if (previous <= 1) {
            // Duration cap reached — stop; onstop emits the clip as usual.
            clearCountdown();
            recorderRef.current?.stop();
            return 0;
          }
          return previous - 1;
        });
      }, 1000);
    } catch {
      setState("idle");
      setMicError(
        "Microphone is unavailable. You can type the observation instead.",
      );
    }
  }

  function stopRecording() {
    clearCountdown();
    if (recorderRef.current?.state === "recording") {
      recorderRef.current.stop();
    }
  }

  return (
    <div className="rounded-xl border border-line bg-moss/50 p-4">
      <label className="flex items-start gap-2 text-xs leading-relaxed text-ink-soft">
        <input
          type="checkbox"
          checked={consented}
          onChange={(event) => setConsented(event.target.checked)}
          className="mt-0.5 h-4 w-4 rounded border-line accent-pine"
          aria-label="I consent to this device's microphone recording this turn"
        />
        <span>
          I consent to recording this turn with the device microphone. The
          audio is used only to produce a written transcript and is not
          stored.
        </span>
      </label>
      <div className="mt-3 flex flex-wrap items-center gap-3">
        {state === "recording" ? (
          <Button
            variant="secondary"
            onClick={stopRecording}
            aria-label="Stop recording"
          >
            Stop recording
          </Button>
        ) : (
          <Button
            onClick={startRecording}
            disabled={disabled || !consented}
            aria-label="Start recording this turn"
          >
            Record turn
          </Button>
        )}
        {state === "recording" && (
          <p
            className="flex items-center gap-2 text-sm font-semibold text-red"
            role="status"
            aria-live="polite"
          >
            <span
              aria-hidden="true"
              className="inline-block h-2.5 w-2.5 animate-pulse rounded-full bg-red"
            />
            Recording — speak now ({secondsLeft}s left, max {MAX_TURN_SECONDS}s)
          </p>
        )}
      </div>
      {micError && (
        <p className="mt-2 text-xs font-medium text-red" role="alert">
          {micError}
        </p>
      )}
      {!consented && state === "idle" && (
        <p className="mt-2 text-xs text-ink-soft">
          Tick the consent box to enable the microphone — or simply type below.
        </p>
      )}
    </div>
  );
}
