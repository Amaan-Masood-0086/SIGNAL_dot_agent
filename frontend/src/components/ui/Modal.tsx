"use client";

import { useEffect, useRef, type ReactNode } from "react";

import { Button } from "@/src/components/ui/Button";

interface ModalProps {
  open: boolean;
  title: string;
  onClose: () => void;
  children: ReactNode;
}

// MUST NOT use alert()/confirm() (web-development.md MUST-NOT #14) — modals
// instead. Escape closes; focus moves into the dialog on open.
export function Modal({ open, title, onClose, children }: ModalProps) {
  const panelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    panelRef.current?.focus();
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div
        className="absolute inset-0 bg-black/40"
        aria-hidden="true"
        onClick={onClose}
      />
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-label={title}
        tabIndex={-1}
        className="relative w-full max-w-md rounded-xl border border-line bg-surface p-6 shadow-lg focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-pine"
      >
        <h2 className="font-display text-lg font-semibold text-ink">{title}</h2>
        <div className="mt-3 text-sm text-ink-soft">{children}</div>
        <div className="mt-5 flex justify-end">
          <Button variant="secondary" onClick={onClose} aria-label={`Close ${title}`}>
            Close
          </Button>
        </div>
      </div>
    </div>
  );
}
