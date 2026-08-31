"use client";

import { useState } from "react";

import { Badge } from "@/src/components/ui/Badge";
import { Button } from "@/src/components/ui/Button";
import { Input } from "@/src/components/ui/Input";
import type { CredentialStatus, ProviderStatus } from "@/src/lib/api/admin";

interface AdminProvidersPanelProps {
  initialStatuses: ProviderStatus[];
  initialCredentials: CredentialStatus[];
}

const PROVIDER_LABELS: Record<string, string> = {
  stt: "Speech-to-text (Azure)",
  llm: "LLM provider",
};

function sourceBadge(status: ProviderStatus | undefined) {
  if (!status?.configured) {
    return <Badge tone="neutral">Not configured</Badge>;
  }
  return status.source === "ui" ? (
    <Badge tone="success">Configured via UI</Badge>
  ) : (
    <Badge tone="warning">Configured via env</Badge>
  );
}

// ADR-10 credential management surface. Write-only by contract:
// - inputs ALWAYS start empty — never pre-filled with a real value;
// - after save, only the returned masked suffix + timestamp are shown;
// - nothing typed is ever echoed back to the screen.
export function AdminProvidersPanel({
  initialStatuses,
  initialCredentials,
}: AdminProvidersPanelProps) {
  const [statuses, setStatuses] = useState(initialStatuses);
  const [credentials, setCredentials] = useState(initialCredentials);
  const [drafts, setDrafts] = useState<Record<string, string>>({ stt: "", llm: "" });
  const [busy, setBusy] = useState<string | null>(null);
  const [messages, setMessages] = useState<Record<string, string>>({});

  async function refresh() {
    try {
      const [statusResp, credentialResp] = await Promise.all([
        fetch("/api/admin/providers"),
        fetch("/api/admin/credentials"),
      ]);
      if (statusResp.ok) {
        setStatuses((await statusResp.json()).providers);
      }
      if (credentialResp.ok) {
        setCredentials((await credentialResp.json()).providers);
      }
    } catch {
      // Status refresh is best-effort; the next render shows stale data.
    }
  }

  async function save(provider: string) {
    const value = drafts[provider]?.trim();
    if (!value || busy) return;
    setBusy(`save-${provider}`);
    setMessages((m) => ({ ...m, [provider]: "" }));
    try {
      const resp = await fetch(`/api/admin/credentials/${provider}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ value }),
      });
      const payload = await resp.json();
      if (!resp.ok) {
        setMessages((m) => ({ ...m, [provider]: payload.detail ?? "Save failed" }));
        return;
      }
      // The response carries ONLY masked_suffix + updated_at. Clear the
      // draft so the typed value exists nowhere on screen.
      setDrafts((d) => ({ ...d, [provider]: "" }));
      setMessages((m) => ({
        ...m,
        [provider]: `Saved — stored credential now ends in …${payload.result.masked_suffix}`,
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
      const resp = await fetch(`/api/admin/credentials/${provider}`, {
        method: "DELETE",
      });
      const payload = await resp.json();
      if (!resp.ok) {
        setMessages((m) => ({ ...m, [provider]: payload.detail ?? "Remove failed" }));
        return;
      }
      setMessages((m) => ({
        ...m,
        [provider]: "Stored credential deactivated — falling back to the environment variable.",
      }));
      await refresh();
    } catch {
      setMessages((m) => ({ ...m, [provider]: "Remove failed" }));
    } finally {
      setBusy(null);
    }
  }

  async function test(provider: string) {
    if (busy) return;
    setBusy(`test-${provider}`);
    try {
      const resp = await fetch(`/api/admin/providers/${provider}/test`, {
        method: "POST",
      });
      const payload = await resp.json();
      if (!resp.ok) {
        setMessages((m) => ({ ...m, [provider]: payload.detail ?? "Test failed" }));
        return;
      }
      setMessages((m) => ({
        ...m,
        [provider]: payload.result.success
          ? "Connection OK — provider accepted the active credential."
          : `Connection failed: ${payload.result.detail}`,
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
          <section
            key={provider}
            aria-label={`${PROVIDER_LABELS[provider]} credential management`}
            className="rounded-xl border border-line bg-surface p-5"
          >
            <div className="flex flex-wrap items-center gap-2">
              <h3 className="mr-auto font-display text-lg font-semibold text-ink">
                {PROVIDER_LABELS[provider]}
              </h3>
              {sourceBadge(status)}
            </div>
            <p className="mt-1 text-xs text-ink-soft">
              {status?.detail ?? "Status unavailable"}
            </p>

            {credential?.is_active && (
              <p className="mt-3 rounded-lg bg-moss/60 p-3 text-xs text-ink">
                Stored credential active — ends in{" "}
                <span className="font-semibold">…{credential.masked_suffix}</span>
                {credential.updated_at && (
                  <span className="text-ink-soft">
                    {" "}
                    · saved {credential.updated_at.slice(0, 10)}
                  </span>
                )}
              </p>
            )}

            <div className="mt-4">
              <Input
                id={`credential-${provider}`}
                label={
                  credential?.is_active
                    ? "Replace the stored key"
                    : "Store a new key (starts empty — never pre-filled)"
                }
                type="password"
                autoComplete="off"
                value={drafts[provider] ?? ""}
                onChange={(event) =>
                  setDrafts((d) => ({ ...d, [provider]: event.target.value }))
                }
                placeholder="Paste the provider key"
              />
            </div>

            <div className="mt-3 flex flex-wrap items-center gap-2">
              <Button
                onClick={() => void save(provider)}
                disabled={busy !== null || !(drafts[provider] ?? "").trim()}
                aria-label={`Save ${PROVIDER_LABELS[provider]} credential`}
              >
                {busy === `save-${provider}` ? "Saving…" : "Save"}
              </Button>
              <Button
                variant="secondary"
                onClick={() => void test(provider)}
                disabled={busy !== null}
                aria-label={`Test ${PROVIDER_LABELS[provider]} connection`}
              >
                {busy === `test-${provider}` ? "Testing…" : "Test connection"}
              </Button>
              {credential?.is_active && (
                <Button
                  variant="secondary"
                  onClick={() => void remove(provider)}
                  disabled={busy !== null}
                  aria-label={`Deactivate stored ${PROVIDER_LABELS[provider]} credential`}
                >
                  {busy === `remove-${provider}` ? "Removing…" : "Deactivate"}
                </Button>
              )}
            </div>

            {messages[provider] && (
              <p className="mt-3 text-xs font-medium text-ink" role="status">
                {messages[provider]}
              </p>
            )}
          </section>
        );
      })}
    </div>
  );
}
