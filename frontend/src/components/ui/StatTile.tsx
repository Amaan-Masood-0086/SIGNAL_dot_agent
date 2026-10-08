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
    <div className="metric">
      <p className="metric-label">
        {label}
      </p>
      <p className={`metric-value ${t.value}`}>
        {value}
      </p>
      {hint && <p className="metric-hint">{hint}</p>}
    </div>
  );
}
