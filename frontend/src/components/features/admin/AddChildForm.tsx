"use client";

import { useState } from "react";

import { Alert } from "@/src/components/ui/Alert";
import { Button } from "@/src/components/ui/Button";
import { Input } from "@/src/components/ui/Input";
import {
  InstitutionPicker,
  useInstitutions,
} from "@/src/components/features/admin/InstitutionPicker";
import { createChildForInstitution } from "@/src/lib/api/admin-client";

/**
 * Register a child from the admin console, under an EXPLICITLY named
 * institution.
 *
 * The caretaker intake form takes no institution: it derives one from the
 * signed token, which is correct there. It cannot work here — a system-level
 * admin belongs to the NextaSol tenant, not to any institution that delivers
 * care, so a child created that way would be filed under the system tenant.
 * Naming the institution is what turns an unsafe shortcut into a real
 * capability.
 *
 * ADR-02 is enforced identically to the caretaker path: a confirmed date of
 * birth and an estimated range are mutually exclusive, never both, never a
 * quietly assumed midpoint. When the age is estimated, screening evaluates at
 * the younger bound and grades borderline delays down.
 */
export function AddChildForm({ onCreated }: { onCreated: () => void }) {
  const { items: institutions, reload } = useInstitutions();
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [institutionId, setInstitutionId] = useState("");
  const [confirmed, setConfirmed] = useState(false);
  const [dob, setDob] = useState("");
  const [range, setRange] = useState("");
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  function reset() {
    setName("");
    setInstitutionId("");
    setConfirmed(false);
    setDob("");
    setRange("");
    setNote("");
    setError(null);
  }

  async function submit() {
    if (busy) return;
    setBusy(true);
    setError(null);
    setNotice(null);
    try {
      // Exactly one age representation is sent — never both (ADR-02).
      await createChildForInstitution({
        name: name.trim(),
        institution_id: institutionId,
        dob_confirmed: confirmed,
        dob: confirmed ? dob : null,
        estimated_age_range: confirmed ? null : range.trim(),
        estimated_age_note: confirmed ? null : note.trim() || null,
      });
      setNotice(`${name.trim()} was registered.`);
      reset();
      setOpen(false);
      onCreated();
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : "The child could not be registered.",
      );
    } finally {
      setBusy(false);
    }
  }

  const ready =
    name.trim().length > 0 &&
    institutionId !== "" &&
    (confirmed ? dob !== "" : range.trim().length > 0);

  if (!open) {
    return (
      <div className="space-y-3">
        {notice && <Alert tone="success">{notice}</Alert>}
        <Button onClick={() => setOpen(true)} aria-label="Register a child">
          Register a child
        </Button>
      </div>
    );
  }

  return (
    <section className="rounded-xl border border-line bg-surface p-5">
      <h3 className="font-display text-base font-semibold tracking-tight text-ink">
        Register a child
      </h3>
      <p className="mt-1 max-w-prose text-xs leading-relaxed text-ink-soft">
        Most children in institutional care have no confirmed date of birth.
        Record whichever you actually have — an estimate is not a lesser answer,
        and screening adjusts its confidence for it automatically.
      </p>

      {error && (
        <div className="mt-3">
          <Alert tone="danger">{error}</Alert>
        </div>
      )}

      <div className="mt-4 grid gap-4 sm:grid-cols-2">
        <Input
          id="child-name"
          label="Name"
          value={name}
          maxLength={200}
          onChange={(event) => setName(event.target.value)}
          placeholder="Child's name"
        />
        <div className="sm:col-span-2">
          <InstitutionPicker
            id="child-institution"
            value={institutionId}
            institutions={institutions}
            disabled={busy}
            onChange={setInstitutionId}
            onCreated={reload}
          />
        </div>
      </div>

      <fieldset className="mt-5">
        <legend className="text-sm font-medium text-ink-soft">Age</legend>
        <div className="mt-2 grid gap-3 sm:grid-cols-2">
          <label
            className={`cursor-pointer rounded-lg border p-3 text-sm ${
              !confirmed ? "border-pine bg-moss/50" : "border-line bg-surface"
            }`}
          >
            <input
              type="radio"
              name="age-mode"
              className="sr-only"
              checked={!confirmed}
              onChange={() => setConfirmed(false)}
            />
            <span className="font-semibold text-ink">Estimated age</span>
            <span className="mt-1 block text-xs text-ink-soft">
              No confirmed date of birth. Screening evaluates at the younger bound.
            </span>
          </label>
          <label
            className={`cursor-pointer rounded-lg border p-3 text-sm ${
              confirmed ? "border-pine bg-moss/50" : "border-line bg-surface"
            }`}
          >
            <input
              type="radio"
              name="age-mode"
              className="sr-only"
              checked={confirmed}
              onChange={() => setConfirmed(true)}
            />
            <span className="font-semibold text-ink">Confirmed date of birth</span>
            <span className="mt-1 block text-xs text-ink-soft">
              A documented DOB, not an estimate.
            </span>
          </label>
        </div>

        <div className="mt-3">
          {confirmed ? (
            <Input
              id="child-dob"
              label="Date of birth"
              type="date"
              value={dob}
              onChange={(event) => setDob(event.target.value)}
            />
          ) : (
            <div className="grid gap-3 sm:grid-cols-2">
              <Input
                id="child-range"
                label="Estimated age range"
                value={range}
                maxLength={50}
                onChange={(event) => setRange(event.target.value)}
                placeholder="e.g. 24-30 months"
                hint="A range in months. Screening uses the younger bound."
              />
              <Input
                id="child-note"
                label="How the age was estimated (optional)"
                value={note}
                onChange={(event) => setNote(event.target.value)}
                placeholder="e.g. teeth, height, caretaker recollection"
              />
            </div>
          )}
        </div>
      </fieldset>

      <div className="mt-4 flex flex-wrap gap-2">
        <Button onClick={() => void submit()} disabled={busy || !ready}>
          {busy ? "Registering…" : "Register child"}
        </Button>
        <Button
          variant="secondary"
          disabled={busy}
          onClick={() => {
            setOpen(false);
            reset();
          }}
        >
          Cancel
        </Button>
      </div>
    </section>
  );
}
