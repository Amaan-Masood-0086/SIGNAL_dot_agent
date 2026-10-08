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
  interactive = false,
  onConfirm,
  onCancel,
}: {
  open: boolean;
  title: string;
  description: ReactNode;
  confirmLabel: string;
  tone?: "primary" | "danger";
  pending?: boolean;
  /**
   * The dialog contains a form control (e.g. a required reason), not just
   * text. Two things change: the role becomes `dialog` — ARIA reserves
   * `alertdialog` for messages, and a screen reader announces a form field
   * inside one badly — and focus is left to the content, which will place it
   * on the field rather than the panel.
   */
  interactive?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  const panelRef = useRef<HTMLDialogElement>(null);

  // Callers pass inline arrows, so `onCancel` is a new function on every
  // render. Keeping it in a ref stops the effects below from re-running each
  // time the parent re-renders — which, with a field inside the dialog, stole
  // focus back to the panel on every single keystroke.
  const cancelRef = useRef(onCancel);
  useEffect(() => {
    cancelRef.current = onCancel;
  });

  // Focus moves ONLY on open. Re-running this on every render is what caused
  // the one-character-at-a-time typing bug.
  useEffect(() => {
    const node = panelRef.current;
    if (!open || !node) return;
    const previousFocus = document.activeElement as HTMLElement | null;
    const overflow = document.body.style.overflow;
    node.showModal();
    document.body.style.overflow = "hidden";
    return () => { node.close(); document.body.style.overflow = overflow; previousFocus?.focus(); };
  }, [open]);

  return (
      <dialog
        ref={panelRef}
        role={interactive ? "dialog" : "alertdialog"}
        aria-modal="true"
        aria-label={title}
        tabIndex={-1}
        onCancel={event => { event.preventDefault(); if (!pending) cancelRef.current(); }}
        className="fixed inset-0 m-auto max-h-[90dvh] w-[calc(100%-2rem)] max-w-md overflow-y-auto rounded-xl border border-line bg-surface p-6 text-ink shadow-lg backdrop:bg-ink/40"
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
      </dialog>
  );
}
