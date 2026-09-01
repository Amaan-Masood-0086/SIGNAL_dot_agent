"use client";

import { useEffect, useRef, type ReactNode } from "react";

import { Button } from "@/src/components/ui/Button";

// MUST-NOT #14: never window.confirm(). Privilege changes and deactivations
// route through this instead, so the operator sees WHO is affected and WHAT
// changes before committing. Escape cancels; focus lands on the dialog.
export function ConfirmDialog({
  open,
  title,
  description,
  confirmLabel,
  tone = "primary",
  pending = false,
  onConfirm,
  onCancel,
}: {
  open: boolean;
  title: string;
  description: ReactNode;
  confirmLabel: string;
  tone?: "primary" | "danger";
  pending?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  const panelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    panelRef.current?.focus();
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") onCancel();
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open, onCancel]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-ink/40" aria-hidden="true" onClick={onCancel} />
      <div
        ref={panelRef}
        role="alertdialog"
        aria-modal="true"
        aria-label={title}
        tabIndex={-1}
        className="relative w-full max-w-md rounded-xl border border-line bg-surface p-6 shadow-[0_24px_60px_-20px_rgba(21,40,37,0.4)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-pine"
      >
        <h2 className="font-display text-lg font-semibold text-ink">{title}</h2>
        <div className="mt-2 text-sm leading-relaxed text-ink-soft">{description}</div>
        <div className="mt-6 flex flex-wrap justify-end gap-2">
          <Button variant="secondary" onClick={onCancel} disabled={pending}>
            Cancel
          </Button>
          <Button
            onClick={onConfirm}
            disabled={pending}
            className={
              tone === "danger" ? "bg-red text-white hover:bg-red focus-visible:outline-red" : ""
            }
          >
            {pending ? "Working…" : confirmLabel}
          </Button>
        </div>
      </div>
    </div>
  );
}
