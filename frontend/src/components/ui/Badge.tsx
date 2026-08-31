import type { ReactNode } from "react";

type Tone = "neutral" | "success" | "warning" | "danger";

const toneClasses: Record<Tone, string> = {
  neutral: "bg-moss text-pine-deep",
  success: "bg-pine text-white",
  warning: "bg-amber-soft text-amber",
  danger: "bg-red-soft text-red",
};

export function Badge({
  children,
  tone = "neutral",
}: {
  children: ReactNode;
  tone?: Tone;
}) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-[11px] font-semibold tracking-wide ${toneClasses[tone]}`}
    >
      {children}
    </span>
  );
}
