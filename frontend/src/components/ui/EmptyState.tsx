import type { ReactNode } from "react";

import { Icon, type IconName } from "@/src/components/ui/Icon";

// MUST #9: every list surface ships an explicit empty state that says what
// the emptiness means and what to do about it — never a bare blank panel.
export function EmptyState({
  icon = "children",
  title,
  description,
  action,
}: {
  icon?: IconName;
  title: string;
  description: ReactNode;
  action?: ReactNode;
}) {
  return (
    <div className="flex flex-col items-center rounded-xl border border-dashed border-line bg-surface px-6 py-10 text-center">
      <span className="flex h-11 w-11 items-center justify-center rounded-full bg-moss text-pine">
        <Icon name={icon} className="h-5 w-5" />
      </span>
      <p className="mt-3 font-display text-lg font-semibold text-ink">{title}</p>
      <p className="mt-1.5 max-w-sm text-sm leading-relaxed text-ink-soft">{description}</p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}
