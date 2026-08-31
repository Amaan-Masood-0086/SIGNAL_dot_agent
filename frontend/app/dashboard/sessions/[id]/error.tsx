"use client";

import Link from "next/link";

// MUST #9: explicit error state; MUST-NOT #16: no internal details shown.
export default function SessionError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <main className="mx-auto w-full max-w-2xl p-8">
      <div
        role="alert"
        className="rounded-xl border border-red/15 bg-red-soft p-6"
      >
        <h2 className="font-display text-lg font-semibold text-red">
          Could not load this session
        </h2>
        <p className="mt-2 text-sm text-red">
          {error.message || "Something went wrong while loading."}
        </p>
        <div className="mt-4 flex items-center gap-4">
          <button
            type="button"
            onClick={reset}
            className="cursor-pointer rounded-lg border border-red/30 bg-surface px-4 py-2 text-sm font-semibold text-red transition-colors duration-150 hover:bg-red-soft"
          >
            Try again
          </button>
          <Link href="/dashboard" className="text-sm font-medium text-ink-soft hover:underline">
            Back to dashboard
          </Link>
        </div>
      </div>
    </main>
  );
}
