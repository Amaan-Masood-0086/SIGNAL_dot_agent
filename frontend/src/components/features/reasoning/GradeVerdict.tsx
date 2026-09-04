import type { ReactNode } from "react";

import { gradeMeta, type GradeTone } from "@/src/lib/screening/grade";

const TONE_CLASSES: Record<GradeTone, { panel: string; rule: string; label: string }> = {
  danger: { panel: "border-red/30 bg-red-soft", rule: "bg-red", label: "text-red" },
  warning: { panel: "border-amber/30 bg-amber-soft", rule: "bg-amber", label: "text-amber" },
  pine: { panel: "border-pine/30 bg-moss", rule: "bg-pine", label: "text-pine-deep" },
  neutral: { panel: "border-line bg-surface", rule: "bg-ink-soft", label: "text-ink" },
};

/**
 * The screening outcome, given the weight it actually carries.
 *
 * A grade used to render as a pill identical in size and shape to the
 * "Speech & language" metadata chip beside it, so "High — see a clinician
 * soon" and a domain label read as the same kind of thing. The recommended
 * action is the product's entire output; it leads here, with the grade name
 * as its qualifier and the caveats demoted to chips underneath.
 *
 * ADR-07: this is never phrased as a diagnosis, and the disclaimer is part
 * of the component rather than something a caller can forget to render.
 */
export function GradeVerdict({
  grade,
  children,
}: {
  grade: string | null;
  children?: ReactNode;
}) {
  const meta = gradeMeta(grade);
  const tone = TONE_CLASSES[meta?.tone ?? "neutral"];

  return (
    <div className={`overflow-hidden rounded-xl border ${tone.panel}`}>
      <div aria-hidden="true" className={`h-1 w-full ${tone.rule}`} />
      <div className="p-5">
        <p
          className={`text-[11px] font-bold tracking-[0.14em] uppercase ${tone.label}`}
        >
          {meta ? `${meta.label} concern` : "Screening result"}
        </p>
        <p className="mt-1.5 font-display text-2xl leading-tight font-bold tracking-tight text-ink">
          {meta?.headline ?? "Conclusion reached"}
        </p>
        {meta && (
          <p className="mt-2 max-w-prose text-sm leading-relaxed text-ink-soft">
            {meta.meaning}
          </p>
        )}
        {children}
      </div>
    </div>
  );
}
