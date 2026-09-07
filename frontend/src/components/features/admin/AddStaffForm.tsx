"use client";

import { useState } from "react";

import { Alert } from "@/src/components/ui/Alert";
import { Button } from "@/src/components/ui/Button";
import { Input } from "@/src/components/ui/Input";
import {
  InstitutionPicker,
  useInstitutions,
} from "@/src/components/features/admin/InstitutionPicker";
import { createStaff } from "@/src/lib/api/admin-client";

/**
 * Create a staff account — the capability whose absence made a fresh system
 * unusable. An admin could promote, demote and deactivate people who already
 * existed, but never add one; the only paths were two seed scripts run by
 * someone with database access. With no caretaker, no session can be opened
 * and the screening pipeline cannot run at all.
 *
 * There is no password field, and that is deliberate rather than an
 * oversight. Login does not verify passwords yet (FEAT-12), so a password
 * box here would collect a secret nothing checks and imply a protection the
 * system does not provide. The copy says so plainly instead.
 */
export function AddStaffForm({ onCreated }: { onCreated: () => void }) {
  const { items: institutions, reload } = useInstitutions();
  const [open, setOpen] = useState(false);
  const [email, setEmail] = useState("");
  const [role, setRole] = useState<"caretaker" | "admin">("caretaker");
  const [institutionId, setInstitutionId] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  function reset() {
    setEmail("");
    setRole("caretaker");
    setInstitutionId("");
    setError(null);
  }

  async function submit() {
    if (busy) return;
    setBusy(true);
    setError(null);
    setNotice(null);
    try {
      const created = await createStaff({
        email: email.trim(),
        role,
        institution_id: institutionId,
      });
      setNotice(`${created.email} was added as a ${created.role}.`);
      reset();
      setOpen(false);
      onCreated();
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : "The account could not be created.",
      );
    } finally {
      setBusy(false);
    }
  }

  const ready = email.trim().length > 3 && email.includes("@") && institutionId !== "";

  if (!open) {
    return (
      <div className="space-y-3">
        {notice && <Alert tone="success">{notice}</Alert>}
        <Button onClick={() => setOpen(true)} aria-label="Add a staff account">
          Add staff account
        </Button>
      </div>
    );
  }

  return (
    <section className="rounded-xl border border-line bg-surface p-5">
      <h3 className="font-display text-base font-semibold tracking-tight text-ink">
        Add a staff account
      </h3>
      <p className="mt-1 max-w-prose text-xs leading-relaxed text-ink-soft">
        A caretaker registers children and runs screening sessions at their own
        institution. An admin manages the system and cannot do either.
      </p>

      {error && (
        <div className="mt-3">
          <Alert tone="danger">{error}</Alert>
        </div>
      )}

      <div className="mt-4 grid gap-4 sm:grid-cols-2">
        <Input
          id="staff-email"
          label="Email"
          type="email"
          value={email}
          maxLength={320}
          onChange={(event) => setEmail(event.target.value)}
          placeholder="caretaker@institution.example"
          hint="This is the sign-in identity — there is no separate username."
        />

        <div className="flex flex-col gap-1">
          <label htmlFor="staff-role" className="text-sm font-medium text-ink-soft">
            Role
          </label>
          <select
            id="staff-role"
            value={role}
            onChange={(event) => setRole(event.target.value as "caretaker" | "admin")}
            className="min-h-11 rounded-lg border border-line bg-surface px-3 py-2 text-sm text-ink focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-pine"
          >
            <option value="caretaker">Caretaker — delivers care</option>
            <option value="admin">Admin — manages the system</option>
          </select>
          <p className="text-xs text-ink-soft">
            Every role change is written to the audit chain.
          </p>
        </div>

        <div className="sm:col-span-2">
          <InstitutionPicker
            id="staff-institution"
            value={institutionId}
            institutions={institutions}
            disabled={busy}
            onChange={setInstitutionId}
            onCreated={reload}
          />
        </div>
      </div>

      <div className="mt-4 rounded-lg border border-amber/30 bg-amber-soft p-3">
        <p className="text-xs leading-relaxed text-ink">
          <span className="font-semibold">No password is set.</span> Sign-in does
          not verify passwords in this build, so this account will be able to log
          in with any password until password verification is implemented.
        </p>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        <Button onClick={() => void submit()} disabled={busy || !ready}>
          {busy ? "Creating…" : "Create account"}
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
