"use client";

import { useEffect, useState } from "react";

/**
 * "Working, and here is how long it has been" — for waits whose length
 * genuinely cannot be predicted.
 *
 * Deliberately indeterminate. A screening turn's duration depends on the
 * prompt size and the provider's latency, so a percentage bar would have to
 * invent its own pace; when it reached 100% and nothing had arrived, the
 * wait would feel longer than it actually is and the number would have been
 * a lie. The sweep says "still working". The elapsed counter beside it is
 * the part that carries real information.
 *
 * The counter also makes a failure legible: this call can take the better
 * part of a minute against a slow provider, and a caretaker who watched it
 * reach 40s understands a timeout in a way that a frozen "Thinking…" never
 * allows.
 */
export function ThinkingBar({
  label = "Thinking",
  /** Seconds after which the wait is worth explaining rather than just showing. */
  patienceAfter = 12,
}: {
  label?: string;
  patienceAfter?: number;
}) {
  const [seconds, setSeconds] = useState(0);

  useEffect(() => {
    const started = Date.now();
    const tick = setInterval(() => {
      setSeconds(Math.floor((Date.now() - started) / 1000));
    }, 1000);
    return () => clearInterval(tick);
  }, []);

  return (
    <div role="status" aria-live="polite" className="w-full">
      <div className="flex items-center gap-2">
        <span className="text-xs font-semibold text-pine">
          {label}… {seconds}s
        </span>
      </div>
      <div
        aria-hidden="true"
        className="mt-1.5 h-1 w-full overflow-hidden rounded-full bg-moss"
      >
        <div className="signal-sweep h-full w-1/4 rounded-full bg-pine" />
      </div>
      {seconds >= patienceAfter && (
        <p className="mt-1.5 text-[11px] leading-relaxed text-ink-soft">
          SIGNAL is checking this against the knowledge base. A turn can take up
          to a minute — the answer is still coming, and nothing is lost if you
          wait.
        </p>
      )}
    </div>
  );
}
