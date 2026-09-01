"use client";

import { useCallback, useEffect, useState } from "react";

import { Badge } from "@/src/components/ui/Badge";
import { Button } from "@/src/components/ui/Button";
import { Input } from "@/src/components/ui/Input";
import {
  getChainStatus,
  listAdminChildren,
  listAdminStaff,
  listAdminUsage,
  listAudit,
  listCredentials,
  listProviderStatuses,
  testProviderConnection,
  updateStaffActive,
  updateStaffRole,
  type AdminChild,
  type AdminStaff,
  type AdminUsage,
  type AuditEntry,
  type ChainStatus,
  type CredentialStatus,
  type ProviderStatus,
} from "@/src/lib/api/admin";

type Tab = "providers" | "children" | "staff" | "audit" | "usage";

const TABS: { id: Tab; label: string }[] = [
  { id: "providers", label: "Providers & credentials" },
  { id: "children", label: "Children" },
  { id: "staff", label: "Staff" },
  { id: "audit", label: "Audit log" },
  { id: "usage", label: "Usage" },
];

// Full admin console (owner request 2026-09-01): one place for provider
// config (key + model), cross-institution children oversight, staff
// management, the tamper-evident audit trail, and cost visibility.
export function AdminConsole() {
  const [tab, setTab] = useState<Tab>("providers");
  const [accessError, setAccessError] = useState(false);

  return (
    <div>
      <div className="flex flex-wrap gap-2" role="tablist" aria-label="Admin sections">
        {TABS.map((t) => (
          <button
            key={t.id}
            role="tab"
            aria-selected={tab === t.id}
            onClick={() => setTab(t.id)}
            className={`rounded-full px-4 py-2 text-sm font-semibold transition-colors ${
              tab === t.id
                ? "bg-pine text-white"
                : "bg-surface text-ink-soft border border-line hover:text-ink"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div className="mt-6">
        {accessError ? (
          <p className="rounded-lg bg-red-soft p-4 text-sm font-medium text-red" role="alert">
            This console needs the admin role. Sign in with the seeded admin
            account (root@signal.example).
          </p>
        ) : (
          <>
            {tab === "providers" && <ProvidersSection onAccessError={() => setAccessError(true)} />}
            {tab === "children" && <ChildrenSection onAccessError={() => setAccessError(true)} />}
            {tab === "staff" && <StaffSection onAccessError={() => setAccessError(true)} />}
            {tab === "audit" && <AuditSection onAccessError={() => setAccessError(true)} />}
            {tab === "usage" && <UsageSection onAccessError={() => setAccessError(true)} />}
          </>
        )}
      </div>
    </div>
  );
}

// ── Providers & credentials ─────────────────────────────────────────────

function ProvidersSection({ onAccessError }: { onAccessError: () => void }) {
  const [statuses, setStatuses] = useState<ProviderStatus[]>([]);
  const [credentials, setCredentials] = useState<CredentialStatus[]>([]);
  const [drafts, setDrafts] = useState<Record<string, { value: string; model: string }>>({
    stt: { value: "", model: "" },
    llm: { value: "", model: "" },
  });
  const [messages, setMessages] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const [s, c] = await Promise.all([listProviderStatuses2(), listCredentials2()]);
      setStatuses(s);
      setCredentials(c);
    } catch {
      onAccessError();
    }
  }, [onAccessError]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  async function save(provider: string) {
    const draft = drafts[provider];
    if (!draft.value.trim() || busy) return;
    setBusy(`save-${provider}`);
    try {
      const resp = await fetch(`/api/admin/credentials/${provider}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          value: draft.value,
          model: provider === "llm" ? draft.model.trim() || null : null,
        }),
      });
      const payload = await resp.json();
      if (!resp.ok) {
        setMessages((m) => ({ ...m, [provider]: payload.detail ?? "Save failed" }));
        return;
      }
      setDrafts((d) => ({ ...d, [provider]: { value: "", model: "" } }));
      setMessages((m) => ({
        ...m,
        [provider]: `Saved — stored credential ends in …${payload.result.masked_suffix}`,
      }));
      await refresh();
    } catch {
      setMessages((m) => ({ ...m, [provider]: "Save failed" }));
    } finally {
      setBusy(null);
    }
  }

  async function remove(provider: string) {
    if (busy) return;
    setBusy(`remove-${provider}`);
    try {
      const resp = await fetch(`/api/admin/credentials/${provider}`, { method: "DELETE" });
      const payload = await resp.json();
      setMessages((m) => ({
        ...m,
        [provider]: resp.ok
          ? "Deactivated — falling back to the environment variable."
          : payload.detail ?? "Remove failed",
      }));
      await refresh();
    } finally {
      setBusy(null);
    }
  }

  async function test(provider: string) {
    if (busy) return;
    setBusy(`test-${provider}`);
    try {
      const result = await testProviderConnection2(provider);
      setMessages((m) => ({
        ...m,
        [provider]: result.success
          ? "Connection OK — provider accepted the active credential."
          : `Connection failed: ${result.detail}`,
      }));
    } catch {
      setMessages((m) => ({ ...m, [provider]: "Test failed" }));
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="grid gap-4 md:grid-cols-2">
      {(["stt", "llm"] as const).map((provider) => {
        const status = statuses.find((s) => s.provider === provider);
        const credential = credentials.find((c) => c.provider === provider);
        return (
          <section key={provider} className="rounded-xl border border-line bg-surface p-5">
            <div className="flex flex-wrap items-center gap-2">
              <h3 className="mr-auto font-display text-lg font-semibold text-ink">
                {provider === "stt" ? "Speech-to-text (Azure)" : "LLM provider"}
              </h3>
              {status?.configured ? (
                status.source === "ui" ? (
                  <Badge tone="success">Configured via UI</Badge>
                ) : (
                  <Badge tone="warning">Configured via env</Badge>
                )
              ) : (
                <Badge tone="neutral">Not configured</Badge>
              )}
            </div>
            <p className="mt-1 text-xs text-ink-soft">{status?.detail}</p>

            {credential?.is_active && (
              <p className="mt-3 rounded-lg bg-moss/60 p-3 text-xs text-ink">
                Stored key active — ends in{" "}
                <span className="font-semibold">…{credential.masked_suffix}</span>
                {credential.model_name && (
                  <span className="text-ink-soft"> · model: {credential.model_name}</span>
                )}
                {credential.updated_at && (
                  <span className="text-ink-soft"> · saved {credential.updated_at.slice(0, 10)}</span>
                )}
              </p>
            )}

            <div className="mt-4 space-y-3">
              <Input
                id={`credential-${provider}`}
                label={credential?.is_active ? "Replace the stored key" : "Store a key (starts empty — never pre-filled)"}
                type="password"
                autoComplete="off"
                value={drafts[provider].value}
                onChange={(e) =>
                  setDrafts((d) => ({ ...d, [provider]: { ...d[provider], value: e.target.value } }))
                }
                placeholder="Paste the provider key"
              />
              {provider === "llm" && (
                <Input
                  id="credential-llm-model"
                  label="Model name (optional — overrides the env model)"
                  value={drafts.llm.model}
                  onChange={(e) =>
                    setDrafts((d) => ({ ...d, llm: { ...d.llm, model: e.target.value } }))
                  }
                  placeholder={credential?.model_name ?? "e.g. gpt-4o-mini"}
                />
              )}
            </div>

            <div className="mt-3 flex flex-wrap items-center gap-2">
              <Button
                onClick={() => void save(provider)}
                disabled={busy !== null || !drafts[provider].value.trim()}
              >
                {busy === `save-${provider}` ? "Saving…" : "Save"}
              </Button>
              <Button variant="secondary" onClick={() => void test(provider)} disabled={busy !== null}>
                {busy === `test-${provider}` ? "Testing…" : "Test connection"}
              </Button>
              {credential?.is_active && (
                <Button variant="secondary" onClick={() => void remove(provider)} disabled={busy !== null}>
                  Deactivate
                </Button>
              )}
            </div>
            {messages[provider] && (
              <p className="mt-3 text-xs font-medium text-ink" role="status">{messages[provider]}</p>
            )}
          </section>
        );
      })}
    </div>
  );
}

// ── Children oversight ──────────────────────────────────────────────────

function ChildrenSection({ onAccessError }: { onAccessError: () => void }) {
  const [data, setData] = useState<{ items: AdminChild[]; total: number } | null>(null);

  useEffect(() => {
    listAdminChildren()
      .then(setData)
      .catch(onAccessError);
  }, [onAccessError]);

  if (!data) return <p className="text-sm text-ink-soft">Loading…</p>;
  return (
    <section className="rounded-xl border border-line bg-surface p-5">
      <h3 className="font-display text-lg font-semibold text-ink">
        All children across institutions ({data.total})
      </h3>
      <p className="mt-1 text-xs text-ink-soft">
        System-level oversight roster — read-only. Caretaker-facing surfaces
        remain strictly institution-scoped.
      </p>
      <ul className="mt-4 space-y-3">
        {data.items.map((child) => (
          <li key={child.id} className="flex flex-wrap items-center gap-3 rounded-lg border border-line p-3">
            <div className="mr-auto">
              <p className="text-sm font-semibold text-ink">{child.name}</p>
              <p className="text-xs text-ink-soft">
                {child.institution_name} ·{" "}
                {child.dob_confirmed ? `Born ${child.dob}` : `Age ${child.estimated_age_range}`} ·
                Intake {child.intake_date}
              </p>
            </div>
            <Badge tone={child.dob_confirmed ? "neutral" : "warning"}>
              {child.dob_confirmed ? "Confirmed DOB" : "Estimated age"}
            </Badge>
          </li>
        ))}
      </ul>
    </section>
  );
}

// ── Staff management ────────────────────────────────────────────────────

function StaffSection({ onAccessError }: { onAccessError: () => void }) {
  const [staff, setStaff] = useState<AdminStaff[] | null>(null);
  const [message, setMessage] = useState("");

  const refresh = useCallback(() => {
    listAdminStaff()
      .then((d) => setStaff(d.items))
      .catch(onAccessError);
  }, [onAccessError]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  async function act(fn: () => Promise<unknown>, ok: string) {
    try {
      await fn();
      setMessage(ok);
      refresh();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Action failed");
    }
  }

  if (!staff) return <p className="text-sm text-ink-soft">Loading…</p>;
  return (
    <section className="rounded-xl border border-line bg-surface p-5">
      <h3 className="font-display text-lg font-semibold text-ink">Staff ({staff.length})</h3>
      <ul className="mt-4 space-y-3">
        {staff.map((s) => (
          <li key={s.id} className="flex flex-wrap items-center gap-3 rounded-lg border border-line p-3">
            <div className="mr-auto">
              <p className="text-sm font-semibold text-ink">{s.email}</p>
              <p className="text-xs text-ink-soft">since {s.created_at.slice(0, 10)}</p>
            </div>
            <Badge tone={s.role === "admin" ? "success" : "neutral"}>{s.role}</Badge>
            {!s.is_active && <Badge tone="warning">deactivated</Badge>}
            <Button
              variant="secondary"
              onClick={() =>
                void act(
                  () => updateStaffRole(s.id, s.role === "admin" ? "caretaker" : "admin"),
                  `Role updated for ${s.email}`,
                )
              }
            >
              {s.role === "admin" ? "Demote" : "Promote"}
            </Button>
            <Button
              variant="secondary"
              onClick={() =>
                void act(
                  () => updateStaffActive(s.id, !s.is_active),
                  s.is_active ? `Deactivated ${s.email}` : `Reactivated ${s.email}`,
                )
              }
            >
              {s.is_active ? "Deactivate" : "Reactivate"}
            </Button>
          </li>
        ))}
      </ul>
      {message && <p className="mt-3 text-xs font-medium text-ink" role="status">{message}</p>}
    </section>
  );
}

// ── Audit log ───────────────────────────────────────────────────────────

function AuditSection({ onAccessError }: { onAccessError: () => void }) {
  const [data, setData] = useState<{ items: AuditEntry[]; total: number } | null>(null);
  const [chain, setChain] = useState<ChainStatus | null>(null);
  const [page, setPage] = useState(1);

  useEffect(() => {
    listAudit({ page })
      .then(setData)
      .catch(onAccessError);
  }, [page, onAccessError]);

  useEffect(() => {
    getChainStatus()
      .then(setChain)
      .catch(() => setChain(null));
  }, []);

  if (!data) return <p className="text-sm text-ink-soft">Loading…</p>;
  return (
    <section className="rounded-xl border border-line bg-surface p-5">
      <div className="flex flex-wrap items-center gap-3">
        <h3 className="mr-auto font-display text-lg font-semibold text-ink">
          Audit log ({data.total} entries)
        </h3>
        {chain &&
          (chain.chain_intact ? (
            <Badge tone="success">Hash chain intact · {chain.entries_checked} checked</Badge>
          ) : (
            <Badge tone="danger">
              CHAIN BROKEN at sequence {chain.first_broken_sequence}
            </Badge>
          ))}
      </div>
      <ul className="mt-4 space-y-2">
        {data.items.map((entry) => (
          <li key={entry.id} className="rounded-lg border border-line p-3 text-xs">
            <span className="font-semibold text-ink">#{entry.sequence} {entry.action}</span>
            <span className="text-ink-soft">
              {" "}· {entry.resource_type}/{entry.resource_id.slice(0, 8)}… ·{" "}
              {entry.timestamp.replace("T", " ").slice(0, 19)}
            </span>
          </li>
        ))}
      </ul>
      <div className="mt-4 flex items-center gap-2">
        <Button variant="secondary" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
          Previous
        </Button>
        <span className="text-xs text-ink-soft">Page {page}</span>
        <Button
          variant="secondary"
          disabled={data.items.length < 25}
          onClick={() => setPage((p) => p + 1)}
        >
          Next
        </Button>
      </div>
    </section>
  );
}

// ── Usage ───────────────────────────────────────────────────────────────

function UsageSection({ onAccessError }: { onAccessError: () => void }) {
  const [usage, setUsage] = useState<AdminUsage | null>(null);

  useEffect(() => {
    listAdminUsage()
      .then(setUsage)
      .catch(onAccessError);
  }, [onAccessError]);

  if (!usage) return <p className="text-sm text-ink-soft">Loading…</p>;
  return (
    <section className="rounded-xl border border-line bg-surface p-5">
      <h3 className="font-display text-lg font-semibold text-ink">
        Provider usage — {usage.total.calls} calls
        {usage.total.estimated_cost !== null && (
          <span className="text-ink-soft"> · est. ${usage.total.estimated_cost.toFixed(4)}</span>
        )}
      </h3>
      <div className="mt-4 grid gap-4 md:grid-cols-2">
        <div>
          <h4 className="text-sm font-semibold text-ink">By staff</h4>
          <ul className="mt-2 space-y-2">
            {usage.by_staff.map((row) => (
              <li key={row.staff_id} className="rounded-lg border border-line p-3 text-xs">
                <span className="font-semibold text-ink">{row.email}</span>
                <span className="text-ink-soft"> · {row.calls} calls</span>
              </li>
            ))}
            {usage.by_staff.length === 0 && (
              <li className="text-xs text-ink-soft">No provider calls yet.</li>
            )}
          </ul>
        </div>
        <div>
          <h4 className="text-sm font-semibold text-ink">By institution</h4>
          <ul className="mt-2 space-y-2">
            {usage.by_institution.map((row) => (
              <li key={row.institution_id} className="rounded-lg border border-line p-3 text-xs">
                <span className="font-semibold text-ink">{row.name}</span>
                <span className="text-ink-soft"> · {row.calls} calls</span>
              </li>
            ))}
            {usage.by_institution.length === 0 && (
              <li className="text-xs text-ink-soft">No provider calls yet.</li>
            )}
          </ul>
        </div>
      </div>
    </section>
  );
}

// ── same-origin helpers (proxy routes) ─────────────────────────────────

async function listProviderStatuses2(): Promise<ProviderStatus[]> {
  const resp = await fetch("/api/admin/providers");
  if (!resp.ok) throw new Error("providers failed");
  return (await resp.json()).providers;
}

async function listCredentials2(): Promise<CredentialStatus[]> {
  const resp = await fetch("/api/admin/credentials");
  if (!resp.ok) throw new Error("credentials failed");
  return (await resp.json()).providers;
}

async function testProviderConnection2(
  provider: string,
): Promise<{ success: boolean; detail: string }> {
  const resp = await fetch(`/api/admin/providers/${provider}/test`, { method: "POST" });
  const payload = await resp.json();
  if (!resp.ok) throw new Error(payload.detail ?? "test failed");
  return payload.result;
}
