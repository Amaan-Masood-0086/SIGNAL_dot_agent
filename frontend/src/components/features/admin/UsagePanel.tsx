"use client";

import { useEffect, useState } from "react";

import { Alert } from "@/src/components/ui/Alert";
import { EmptyState } from "@/src/components/ui/EmptyState";
import { SkeletonRows } from "@/src/components/ui/Skeleton";
import { StatTile } from "@/src/components/ui/StatTile";
import { fetchUsage } from "@/src/lib/api/admin-client";
import type { AdminUsage } from "@/src/lib/api/admin-schemas";

interface Row {
  id: string;
  label: string;
  calls: number;
  cost: number | null;
}

function money(value: number | null): string {
  return value === null ? "—" : `$${value.toFixed(4)}`;
}

export function UsagePanel() {
  const [usage, setUsage] = useState<AdminUsage | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchUsage()
      .then(setUsage)
      .catch((caught) =>
        setError(caught instanceof Error ? caught.message : "Usage data is unavailable."),
      );
  }, []);

  if (error) return <Alert tone="danger">{error}</Alert>;

  if (!usage) {
    return (
      <div className="space-y-4">
        <SkeletonRows rows={3} />
      </div>
    );
  }

  const staffRows: Row[] = usage.by_staff.map((row) => ({
    id: row.staff_id,
    label: row.email,
    calls: row.calls,
    cost: row.estimated_cost,
  }));
  const institutionRows: Row[] = usage.by_institution.map((row) => ({
    id: row.institution_id,
    label: row.name,
    calls: row.calls,
    cost: row.estimated_cost,
  }));

  const busiest = staffRows[0];

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatTile label="Provider calls" value={usage.total.calls} tone="pine" />
        <StatTile
          label="Estimated cost"
          value={money(usage.total.estimated_cost)}
          hint="Sum of per-call estimates, not a provider invoice"
          tone={(usage.total.estimated_cost ?? 0) > 0 ? "amber" : "neutral"}
        />
        <StatTile label="Institutions billing" value={institutionRows.length} />
        <StatTile
          label="Busiest account"
          value={busiest ? busiest.calls : 0}
          hint={busiest ? `calls — ${busiest.label}` : "No calls recorded yet"}
        />
      </div>

      {/* The two providers are separate companies with separate invoices, so
          the combined total above is not reconcilable against either bill on
          its own. This is the split that is. */}
      <section className="rounded-xl border border-line bg-surface p-5">
        <h2 className="font-display text-lg font-semibold tracking-tight text-ink">
          By provider
        </h2>
        <p className="mt-1 text-xs leading-relaxed text-ink-soft">
          Speech-to-text and the language model are billed by different vendors.
          Reconcile each column against that vendor&rsquo;s own invoice — the
          combined total above matches neither.
        </p>
        {/* The counts come straight from the ledger and are exact. The costs
            are model output, and the model only matches reality if the rates
            were set for the vendor actually in use — saying so is the
            difference between an estimate and a wrong number. */}
        <p className="mt-2 rounded-lg bg-amber-soft px-3 py-2 text-[11px] leading-relaxed text-amber">
          <span className="font-semibold">Counts are exact; costs are estimates.</span>{" "}
          Cost is computed from per-million token rates and an audio-duration
          guess, using whatever rates are configured in the environment. If the
          provider was changed without updating
          {" "}<code className="font-mono">LLM_COST_PER_MILLION_INPUT</code>/
          <code className="font-mono">OUTPUT</code>, the money column is priced
          for the previous vendor. Treat the vendor&rsquo;s invoice as the
          source of truth, and this page as the early-warning signal it was
          built to be.
        </p>
        <dl className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
          {(
            [
              {
                key: "llm" as const,
                label: "Language model",
                note: "Reasoning and explanation calls",
              },
              {
                key: "stt" as const,
                label: "Speech-to-text",
                note: "One call per transcribed turn",
              },
            ]
          ).map((provider) => {
            const row = usage.by_provider[provider.key];
            return (
              <div
                key={provider.key}
                className="rounded-lg border border-line px-4 py-3"
              >
                <dt className="text-[11px] font-bold tracking-[0.12em] text-ink-soft uppercase">
                  {provider.label}
                </dt>
                <dd className="mt-1.5 flex flex-wrap items-baseline gap-x-3">
                  <span className="font-display text-2xl leading-none font-bold tracking-tight text-ink">
                    {row.calls}
                  </span>
                  <span className="text-xs text-ink-soft">
                    {row.calls === 1 ? "call" : "calls"}
                  </span>
                  <span
                    className={`ml-auto font-display text-lg leading-none font-bold ${
                      (row.estimated_cost ?? 0) > 0 ? "text-amber" : "text-ink-soft"
                    }`}
                  >
                    {money(row.estimated_cost)}
                  </span>
                </dd>
                <p className="mt-1.5 text-[11px] text-ink-soft">
                  {row.calls === 0 ? "Nothing spent — no calls recorded" : provider.note}
                </p>
              </div>
            );
          })}
        </dl>
      </section>

      <Alert tone="info">
        These numbers are the reporting half of the cost-abuse control: rate limits
        cap how fast paid calls can be made, and this breakdown makes an unusual
        pattern visible before it becomes a bill.
      </Alert>

      <div className="grid gap-4 lg:grid-cols-2">
        <UsageTable
          title="By staff member"
          description="Who is spending the provider budget."
          columnLabel="Account"
          rows={staffRows}
        />
        <UsageTable
          title="By institution"
          description="Where the spend is concentrated."
          columnLabel="Institution"
          rows={institutionRows}
        />
      </div>
    </div>
  );
}

function UsageTable({
  title,
  description,
  columnLabel,
  rows,
}: {
  title: string;
  description: string;
  columnLabel: string;
  rows: Row[];
}) {
  const max = Math.max(1, ...rows.map((row) => row.calls));

  return (
    <section className="rounded-xl border border-line bg-surface">
      <header className="border-b border-line px-5 py-4">
        <h2 className="font-display text-lg font-semibold tracking-tight text-ink">{title}</h2>
        <p className="mt-1 text-xs text-ink-soft">{description}</p>
      </header>
      <div className="p-5">
        {rows.length === 0 ? (
          <EmptyState
            icon="usage"
            title="No provider calls yet"
            description="Once a voice transcription or a reasoning run happens, the spend appears here."
          />
        ) : (
          <ul className="space-y-3">
            {rows.map((row) => (
              <li key={row.id}>
                <div className="flex flex-wrap items-baseline justify-between gap-2">
                  <span className="min-w-0 truncate text-sm font-semibold text-ink" title={row.label}>
                    {row.label}
                  </span>
                  <span className="text-xs text-ink-soft">
                    {row.calls} calls · {money(row.cost)}
                  </span>
                </div>
                {/* Proportional bar: the shape of the spend is the point, so
                    it is rendered, not just tabulated. Hidden from screen
                    readers — the numbers above already say it. */}
                <div
                  className="mt-1.5 h-1.5 w-full overflow-hidden rounded-full bg-line"
                  aria-hidden="true"
                >
                  <div
                    className="h-full rounded-full bg-pine"
                    style={{ width: `${Math.round((row.calls / max) * 100)}%` }}
                  />
                </div>
                <span className="sr-only">
                  {columnLabel} {row.label}: {row.calls} calls
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}
