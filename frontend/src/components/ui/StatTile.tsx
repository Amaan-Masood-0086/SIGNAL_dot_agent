import type { ReactNode } from "react";

type Tone = "neutral" | "pine" | "amber" | "red";

const toneClasses: Record<Tone, { value: string; rule: string }> = {
  neutral: { value: "text-ink", rule: "bg-line" },
  pine: { value: "text-pine-deep", rule: "bg-pine" },
  amber: { value: "text-amber", rule: "bg-amber" },
  red: { value: "text-red", rule: "bg-red" },
};

// A single number with its label and one line of meaning. Deliberately flat
// (no shadow) so a row of tiles reads as one instrument panel rather than
// six competing cards.
export function StatTile({
  label,
  value,
  hint,
  tone = "neutral",
}: {
  label: string;
  value: ReactNode;
  hint?: ReactNode;
  tone?: Tone;
}) {
  const t = toneClasses[tone];
  return (
    <div className="relative overflow-hidden rounded-xl border border-line bg-surface p-4">
      <span aria-hidden="true" className={`absolute inset-x-0 top-0 h-0.5 ${t.rule}`} />
      <p className="text-[11px] font-semibold tracking-[0.12em] text-ink-soft uppercase">
        {label}
      </p>
      <p className={`mt-2 font-display text-3xl leading-none font-bold tracking-tight ${t.value}`}>
        {value}
      </p>
      {hint && <p className="mt-2 text-xs leading-relaxed text-ink-soft">{hint}</p>}
    </div>
  );
}
