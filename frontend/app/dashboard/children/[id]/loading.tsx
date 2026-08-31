// MUST #9: explicit loading state on data-fetching pages.
export default function ChildProfileLoading() {
  return (
    <main className="mx-auto w-full max-w-2xl p-8" aria-busy="true" aria-live="polite">
      <div className="rounded-xl border border-line bg-surface p-6 shadow-sm">
        <div className="h-5 w-48 animate-pulse rounded bg-moss" />
        <div className="mt-4 space-y-3">
          <div className="h-4 w-full animate-pulse rounded bg-paper" />
          <div className="h-4 w-2/3 animate-pulse rounded bg-paper" />
        </div>
        <p className="mt-4 text-xs text-ink-soft">Loading child profile…</p>
      </div>
    </main>
  );
}
