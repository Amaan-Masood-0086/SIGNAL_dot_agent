import type { ReactNode } from "react";

import { Icon } from "@/src/components/ui/Icon";

type Tone = "info" | "success" | "warning" | "danger";

const toneClasses: Record<Tone, string> = {
  info: "border-line bg-moss/50 text-ink",
  success: "border-pine/30 bg-moss text-pine-deep",
  warning: "border-amber/30 bg-amber-soft text-amber",
  danger: "border-red/30 bg-red-soft text-red",
};

// Inline status/error messaging. Errors announce themselves (role="alert");
// successes are polite (role="status") so a screen reader is not interrupted.
export function Alert({
  tone = "info",
  children,
}: {
  tone?: Tone;
  children: ReactNode;
}) {
  const assertive = tone === "danger";
  return (
    <div
      role={assertive ? "alert" : "status"}
      className={`flex items-start gap-2.5 rounded-lg border p-3 text-sm leading-relaxed font-medium ${toneClasses[tone]}`}
    >
      <Icon
        name={tone === "success" ? "check" : tone === "info" ? "shield" : "alert"}
        className="mt-0.5 h-4 w-4 shrink-0"
      />
      <span className="min-w-0">{children}</span>
    </div>
  );
}
