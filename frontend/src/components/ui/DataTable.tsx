import type { ReactNode } from "react";

// Wide content scrolls inside its own container — the page body must never
// scroll horizontally on a phone.
export function TableScroll({ children }: { children: ReactNode }) {
  return (
    <div className="-mx-1 overflow-x-auto px-1">
      <div className="min-w-[36rem]">{children}</div>
    </div>
  );
}

export function TableHead({ children }: { children: ReactNode }) {
  return (
    <div className="grid gap-3 border-b border-line px-4 pb-2 text-[11px] font-semibold tracking-[0.1em] text-ink-soft uppercase">
      {children}
    </div>
  );
}

export function TableRow({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={`grid items-center gap-3 border-b border-line/70 px-4 py-3 text-sm last:border-b-0 hover:bg-moss/30 ${className}`}
    >
      {children}
    </div>
  );
}

export function Panel({
  title,
  description,
  actions,
  children,
}: {
  title: string;
  description?: ReactNode;
  actions?: ReactNode;
  children: ReactNode;
}) {
  return (
    <section className="rounded-xl border border-line bg-surface">
      <header className="flex flex-wrap items-start justify-between gap-3 border-b border-line px-5 py-4">
        <div className="min-w-0">
          <h2 className="font-display text-lg font-semibold tracking-tight text-ink">{title}</h2>
          {description && (
            <p className="mt-1 max-w-xl text-xs leading-relaxed text-ink-soft">{description}</p>
          )}
        </div>
        {actions && <div className="flex shrink-0 flex-wrap items-center gap-2">{actions}</div>}
      </header>
      <div className="p-5">{children}</div>
    </section>
  );
}
