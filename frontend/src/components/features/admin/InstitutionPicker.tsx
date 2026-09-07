"use client";

import { useEffect, useState } from "react";

import { Button } from "@/src/components/ui/Button";
import { Input } from "@/src/components/ui/Input";
import { createInstitution, fetchInstitutions } from "@/src/lib/api/admin-client";
import type { Institution } from "@/src/lib/api/admin-schemas";

/**
 * Choose the institution a staff member or child belongs to.
 *
 * Shared by both onboarding forms because the same rule governs both: a
 * system-level admin has no care institution of their own, so the
 * institution is stated explicitly rather than inferred from their token.
 * Filing a real child under the NextaSol system tenant is the "quietly
 * wrong" data the caretaker-only nav guard exists to prevent.
 *
 * Creating one inline matters on a fresh system: the first admin has no
 * institution to pick, and sending them to a different screen to make one
 * turns a two-field form into a dead end.
 */
export function useInstitutions() {
  const [items, setItems] = useState<Institution[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    let cancelled = false;
    fetchInstitutions()
      .then((data) => {
        if (cancelled) return;
        setItems(data.items);
        setError(null);
      })
      .catch((caught: unknown) => {
        if (cancelled) return;
        setItems([]);
        setError(
          caught instanceof Error ? caught.message : "Institutions could not be loaded.",
        );
      });
    return () => {
      cancelled = true;
    };
  }, [reloadKey]);

  return { items, error, reload: () => setReloadKey((k) => k + 1) };
}

export function InstitutionPicker({
  id,
  value,
  institutions,
  disabled,
  onChange,
  onCreated,
}: {
  id: string;
  value: string;
  institutions: Institution[] | null;
  disabled?: boolean;
  onChange: (institutionId: string) => void;
  onCreated: () => void;
}) {
  const [adding, setAdding] = useState(false);
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit() {
    const trimmed = name.trim();
    if (trimmed.length < 2 || busy) return;
    setBusy(true);
    setError(null);
    try {
      const created = await createInstitution(trimmed);
      onChange(created.id);
      onCreated();
      setName("");
      setAdding(false);
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : "The institution could not be created.",
      );
    } finally {
      setBusy(false);
    }
  }

  const empty = institutions !== null && institutions.length === 0;

  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={id} className="text-sm font-medium text-ink-soft">
        Institution
      </label>
      <select
        id={id}
        value={value}
        disabled={disabled || institutions === null || empty}
        onChange={(event) => onChange(event.target.value)}
        className="min-h-11 rounded-lg border border-line bg-surface px-3 py-2 text-sm text-ink focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-pine disabled:opacity-60"
      >
        {institutions === null && <option value="">Loading…</option>}
        {empty && <option value="">No institutions yet — add one below</option>}
        {institutions !== null && !empty && (
          <>
            <option value="">Choose an institution…</option>
            {institutions.map((institution) => (
              <option key={institution.id} value={institution.id}>
                {institution.name}
              </option>
            ))}
          </>
        )}
      </select>
      <p className="text-xs text-ink-soft">
        Records are filed under this institution, not under your admin account.
      </p>

      {adding ? (
        <div className="mt-2 rounded-lg border border-line bg-moss/40 p-3">
          <Input
            id={`${id}-new`}
            label="New institution name"
            value={name}
            autoFocus
            maxLength={200}
            onChange={(event) => setName(event.target.value)}
            placeholder="e.g. Edhi Home, Karachi"
            error={error ?? undefined}
          />
          <div className="mt-2 flex gap-2">
            <Button onClick={() => void submit()} disabled={busy || name.trim().length < 2}>
              {busy ? "Adding…" : "Add institution"}
            </Button>
            <Button
              variant="secondary"
              disabled={busy}
              onClick={() => {
                setAdding(false);
                setName("");
                setError(null);
              }}
            >
              Cancel
            </Button>
          </div>
        </div>
      ) : (
        <button
          type="button"
          onClick={() => setAdding(true)}
          className="mt-1 self-start text-xs font-semibold text-pine hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-pine"
        >
          + Add a new institution
        </button>
      )}
    </div>
  );
}
