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
    <header className="page-header">
      <div className="min-w-0">
        {eyebrow && (
          <p className="page-eyebrow">
            {eyebrow}
          </p>
        )}
        <h1 className="font-display text-ink">
          {title}
        </h1>
        {lede && (
          <p className="page-lede">{lede}</p>
        )}
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
    </header>
  );
}
