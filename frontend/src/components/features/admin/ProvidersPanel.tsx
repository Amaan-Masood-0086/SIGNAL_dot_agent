"use client";

import { useCallback, useEffect, useState } from "react";

import { Alert } from "@/src/components/ui/Alert";
import { Badge } from "@/src/components/ui/Badge";
import { Button } from "@/src/components/ui/Button";
import { ConfirmDialog } from "@/src/components/ui/ConfirmDialog";
import { Input } from "@/src/components/ui/Input";
import { Skeleton } from "@/src/components/ui/Skeleton";
import {
  deleteCredential,
  fetchCredentials,
  fetchProviderStatuses,
  saveCredential,
  testProvider,
} from "@/src/lib/api/admin-client";
import type { CredentialStatus, ProviderStatus } from "@/src/lib/api/admin-schemas";

type Provider = "stt" | "llm";

const PROVIDERS: { id: Provider; title: string; blurb: string }[] = [
  {
    id: "stt",
    title: "Speech-to-text",
    blurb:
      "Transcribes voice observations. Without a key, sessions fall back to text capture — the recorded observation data is identical either way.",
  },
  {
    id: "llm",
    title: "Language model",
    blurb:
      "Drives the reasoning trail behind each flag. Without a key, the synthetic reasoning path is used and results are marked accordingly.",
  },
];

interface Feedback {
  tone: "success" | "warning" | "danger";
  message: string;
}

export function ProvidersPanel() {
  const [statuses, setStatuses] = useState<ProviderStatus[] | null>(null);
  const [credentials, setCredentials] = useState<CredentialStatus[]>([]);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  // A save or a deactivation bumps `reloadKey`, which re-runs this effect —
  // state is only ever set from the resolved promise, and a stale response
  // that lands after a newer request is discarded.
  useEffect(() => {
    let cancelled = false;
    Promise.all([fetchProviderStatuses(), fetchCredentials()])
      .then(([nextStatuses, nextCredentials]) => {
        if (cancelled) return;
        setStatuses(nextStatuses);
        setCredentials(nextCredentials);
        setLoadError(null);
      })
      .catch((error: unknown) => {
        if (cancelled) return;
        setStatuses([]);
        setLoadError(
          error instanceof Error ? error.message : "Provider status is unavailable.",
        );
      });
    return () => {
      cancelled = true;
    };
  }, [reloadKey]);

  const refresh = useCallback(() => setReloadKey((key) => key + 1), []);

  if (statuses === null) {
    return (
      <div className="grid gap-4 lg:grid-cols-2">
        <Skeleton className="h-80 w-full" />
        <Skeleton className="h-80 w-full" />
      </div>
    );
  }

  if (loadError) {
    return <Alert tone="danger">{loadError}</Alert>;
  }

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      {PROVIDERS.map((provider) => (
        <ProviderCard
          key={provider.id}
          id={provider.id}
          title={provider.title}
          blurb={provider.blurb}
          status={statuses.find((entry) => entry.provider === provider.id) ?? null}
          credential={credentials.find((entry) => entry.provider === provider.id) ?? null}
          onChanged={refresh}
        />
      ))}
    </div>
  );
}

function ProviderCard({
  id,
  title,
  blurb,
  status,
  credential,
  onChanged,
}: {
  id: Provider;
  title: string;
  blurb: string;
  status: ProviderStatus | null;
  credential: CredentialStatus | null;
  onChanged: () => void;
}) {
  const [keyDraft, setKeyDraft] = useState("");
  const [modelDraft, setModelDraft] = useState("");
  const [busy, setBusy] = useState<"save" | "test" | "remove" | null>(null);
  const [feedback, setFeedback] = useState<Feedback | null>(null);
  const [confirmRemove, setConfirmRemove] = useState(false);

  const stored = credential?.is_active === true;

  async function run(kind: "save" | "test" | "remove", action: () => Promise<Feedback>) {
    if (busy) return;
    setBusy(kind);
    setFeedback(null);
    try {
      setFeedback(await action());
    } catch (error) {
      setFeedback({
        tone: "danger",
        message: error instanceof Error ? error.message : "The request could not be completed.",
      });
    } finally {
      setBusy(null);
    }
  }

  const onSave = () =>
    run("save", async () => {
      const result = await saveCredential(id, keyDraft, id === "llm" ? modelDraft : null);
      // The field is cleared on success — a key that lingers in a form is a
      // key waiting to be shoulder-surfed or autofilled somewhere else.
      setKeyDraft("");
      setModelDraft("");
      onChanged();
      return {
        tone: "success",
        message: `Saved. The stored key ends in …${result.masked_suffix ?? "****"}${
          result.model_name ? ` and overrides the model to ${result.model_name}` : ""
        }.`,
      };
    });

  const onTest = () =>
    run("test", async () => {
      const result = await testProvider(id);
      return result.success
        ? { tone: "success", message: "Connection OK — the provider accepted the active credential." }
        : { tone: "warning", message: `Connection failed: ${result.detail}` };
    });

  const onRemove = () =>
    run("remove", async () => {
      await deleteCredential(id);
      setConfirmRemove(false);
      onChanged();
      return {
        tone: "success",
        message: "Stored key deactivated. The system falls back to the environment variable.",
      };
    });

  return (
    <section className="flex flex-col rounded-xl border border-line bg-surface">
      <header className="border-b border-line p-5">
        <div className="flex flex-wrap items-center gap-2">
          <h2 className="mr-auto font-display text-lg font-semibold tracking-tight text-ink">
            {title}
          </h2>
          {status?.configured ? (
            <Badge tone={status.source === "ui" ? "success" : "warning"}>
              {status.source === "ui" ? "Key stored in app" : "From environment"}
            </Badge>
          ) : (
            <Badge tone="neutral">Not configured</Badge>
          )}
        </div>
        <p className="mt-1.5 text-xs leading-relaxed text-ink-soft">{blurb}</p>
        {status?.detail && (
          <p className="mt-2 text-xs font-medium text-ink-soft">{status.detail}</p>
        )}
      </header>

      <div className="flex flex-1 flex-col gap-4 p-5">
        {stored && (
          <dl className="rounded-lg bg-moss/60 p-3 text-xs text-ink">
            <div className="flex flex-wrap gap-x-2">
              <dt className="font-semibold">Stored key</dt>
              <dd>ends in …{credential?.masked_suffix ?? "****"}</dd>
            </div>
            {credential?.model_name && (
              <div className="mt-1 flex flex-wrap gap-x-2">
                <dt className="font-semibold">Model override</dt>
                <dd>{credential.model_name}</dd>
              </div>
            )}
            {credential?.updated_at && (
              <div className="mt-1 flex flex-wrap gap-x-2">
                <dt className="font-semibold">Last saved</dt>
                <dd>{credential.updated_at.slice(0, 10)}</dd>
              </div>
            )}
          </dl>
        )}

        <Input
          id={`credential-${id}`}
          label={stored ? "Replace the stored key" : "Store a key"}
          type="password"
          autoComplete="off"
          spellCheck={false}
          value={keyDraft}
          onChange={(event) => setKeyDraft(event.target.value)}
          placeholder="Paste the provider key"
          hint="Write-only: the field starts empty, is never pre-filled, and only the last four characters are ever shown again."
        />

        {id === "llm" && (
          <Input
            id="credential-llm-model"
            label="Model name (optional)"
            value={modelDraft}
            onChange={(event) => setModelDraft(event.target.value)}
            placeholder={credential?.model_name ?? "e.g. gpt-4o-mini"}
            maxLength={120}
            hint="Saved together with the key. Leave blank to keep using the model configured in the environment."
          />
        )}

        {feedback && <Alert tone={feedback.tone}>{feedback.message}</Alert>}

        <div className="mt-auto flex flex-wrap items-center gap-2 pt-1">
          <Button onClick={onSave} disabled={busy !== null || keyDraft.trim().length === 0}>
            {busy === "save" ? "Saving…" : "Save key"}
          </Button>
          <Button variant="secondary" onClick={onTest} disabled={busy !== null}>
            {busy === "test" ? "Testing…" : "Test connection"}
          </Button>
          {stored && (
            <Button
              variant="ghost"
              onClick={() => setConfirmRemove(true)}
              disabled={busy !== null}
              className="text-red hover:bg-red-soft hover:text-red"
            >
              Deactivate
            </Button>
          )}
        </div>
        <p className="text-[11px] leading-relaxed text-ink-soft">
          Test connection fires one real, billed call against whichever
          credential is currently active. It is rate-limited to five attempts
          every five minutes.
        </p>
      </div>

      <ConfirmDialog
        open={confirmRemove}
        title={`Deactivate the stored ${title.toLowerCase()} key?`}
        description={
          <>
            The encrypted key is deactivated, not deleted, and this provider
            falls straight back to the environment variable. If no environment
            key is set, the provider becomes unconfigured and the synthetic
            fallback takes over.
          </>
        }
        confirmLabel="Deactivate key"
        tone="danger"
        pending={busy === "remove"}
        onConfirm={onRemove}
        onCancel={() => setConfirmRemove(false)}
      />
    </section>
  );
}
