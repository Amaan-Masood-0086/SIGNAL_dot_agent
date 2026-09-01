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
