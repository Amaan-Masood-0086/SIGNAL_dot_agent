import type { ReactNode } from "react";

// One consistent page opening across every dashboard surface: eyebrow (where
// am I), title (what is this), lede (what it's for), actions (what to do).
export function PageHeader({
  eyebrow,
  title,
  lede,
  actions,
}: {
  eyebrow?: string;
  title: string;
  lede?: ReactNode;
  actions?: ReactNode;
}) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-4 border-b border-line pb-5">
      <div className="min-w-0">
        {eyebrow && (
          <p className="text-[11px] font-semibold tracking-[0.14em] text-ink-soft uppercase">
            {eyebrow}
          </p>
        )}
        <h1 className="mt-1 font-display text-2xl font-bold tracking-tight text-ink sm:text-3xl">
          {title}
        </h1>
        {lede && (
          <p className="mt-2 max-w-2xl text-sm leading-relaxed text-ink-soft">{lede}</p>
        )}
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
    </div>
  );
}
