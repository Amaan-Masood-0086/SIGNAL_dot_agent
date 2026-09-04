"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Alert } from "@/src/components/ui/Alert";
import { Button } from "@/src/components/ui/Button";
import { ConfirmDialog } from "@/src/components/ui/ConfirmDialog";
import { Input } from "@/src/components/ui/Input";

/**
 * Take a child off the active roster — or put them back.
 *
 * Deliberately worded as "archive", never "delete", because that is what it
 * does: the record and every flag written about it survive. Calling it
 * delete would promise a caretaker something the system does not do, and
 * children's health records carry retention obligations that a button in a
 * roster has no business resolving.
 */
export function ArchiveChild({
  childId,
  childName,
  archivedReason,
}: {
  childId: string;
  childName: string;
  archivedReason: string | null;
}) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [reason, setReason] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const archived = archivedReason !== null;

  async function send(path: string, body?: object) {
    setPending(true);
    setError(null);
    try {
      const response = await fetch(`/api/children/${childId}/${path}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: body ? JSON.stringify(body) : undefined,
      });
      if (!response.ok) {
        const payload = (await response.json().catch(() => ({}))) as {
          detail?: string;
        };
        setError(payload.detail ?? "The change could not be applied.");
        return;
      }
      setOpen(false);
      setReason("");
      router.refresh();
    } catch {
      setError("The change could not be applied.");
    } finally {
      setPending(false);
    }
  }

  if (archived) {
    return (
      <div className="rounded-xl border border-amber/30 bg-amber-soft p-5">
        <p className="text-[11px] font-bold tracking-[0.14em] text-amber uppercase">
          Archived
        </p>
        <p className="mt-1.5 text-sm leading-relaxed text-ink">
          {childName} is not on the active roster. Reason given:{" "}
          <span className="font-semibold">{archivedReason}</span>
        </p>
        <p className="mt-1.5 text-xs leading-relaxed text-ink-soft">
          Nothing was deleted — the profile and every screening result behind
          it are intact, and this can be undone.
        </p>
        {error && (
          <div className="mt-3">
            <Alert tone="danger">{error}</Alert>
          </div>
        )}
        <div className="mt-4">
          <Button
            variant="secondary"
            disabled={pending}
            onClick={() => void send("restore")}
            aria-label={`Return ${childName} to the active roster`}
          >
            {pending ? "Working…" : "Return to the roster"}
          </Button>
        </div>
      </div>
    );
  }

  return (
    <>
      {error && (
        <div className="mb-3">
          <Alert tone="danger">{error}</Alert>
        </div>
      )}
      <Button
        variant="ghost"
        className="text-red hover:bg-red-soft hover:text-red"
        onClick={() => setOpen(true)}
        aria-label={`Archive ${childName}`}
      >
        Archive this child
      </Button>

      <ConfirmDialog
        open={open}
        title={`Archive ${childName}?`}
        description={
          <>
            <span className="block">
              They come off the active roster. Nothing is deleted: the profile,
              the observation sessions and every screening result stay exactly
              as they are, and this can be undone at any time.
            </span>
            <span className="mt-3 block">
              <Input
                id="archive-reason"
                label="Reason"
                autoFocus
                value={reason}
                onChange={(event) => setReason(event.target.value)}
                placeholder="e.g. Duplicate registration, or left the institution"
                maxLength={200}
                hint="Recorded in the audit log — a later reviewer needs to know why this child left the roster."
              />
            </span>
          </>
        }
        confirmLabel="Archive"
        tone="danger"
        interactive
        pending={pending}
        onConfirm={() => void send("archive", { reason: reason.trim() })}
        onCancel={() => {
          setOpen(false);
          setReason("");
          setError(null);
        }}
      />
    </>
  );
}
