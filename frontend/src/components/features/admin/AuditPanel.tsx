"use client";

import { useEffect, useState } from "react";

import { Alert } from "@/src/components/ui/Alert";
import { Badge } from "@/src/components/ui/Badge";
import { Button } from "@/src/components/ui/Button";
import { EmptyState } from "@/src/components/ui/EmptyState";
import { SkeletonRows } from "@/src/components/ui/Skeleton";
import { StatTile } from "@/src/components/ui/StatTile";
import { TableHead, TableRow, TableScroll } from "@/src/components/ui/DataTable";
import { fetchAuditLog, fetchChainStatus } from "@/src/lib/api/admin-client";
import { ADMIN_PAGE_SIZE, type AuditEntry, type ChainStatus } from "@/src/lib/api/admin-schemas";

const COLUMNS = "grid-cols-[4.5rem_minmax(0,1.2fr)_minmax(0,1.2fr)_minmax(0,1fr)]";

// Filter values are a fixed allowlist, matching the shape the proxy accepts.
// A free-text action box would let arbitrary strings into the query.
const ACTIONS: { value: string; label: string }[] = [
  { value: "", label: "All activity" },
  { value: "staff.role_change", label: "Role changed" },
  { value: "staff.deactivate", label: "Staff deactivated" },
  { value: "staff.reactivate", label: "Staff reactivated" },
  { value: "staff.seed_admin", label: "Admin seeded" },
  { value: "credential.store", label: "Credential stored" },
  { value: "credential.deactivate", label: "Credential deactivated" },
  { value: "provider.test_connection", label: "Provider tested" },
  { value: "child.create", label: "Child registered" },
  // Read access (audit F3) — "who opened this record" is now answerable.
  { value: "child.read", label: "Child record opened" },
  { value: "flag.read", label: "Flag opened" },
  { value: "flag.list", label: "Screening history viewed" },
  { value: "admin.children_list", label: "Cross-institution roster viewed" },
  { value: "session.create", label: "Session started" },
  { value: "session.complete", label: "Session completed" },
  { value: "flag.create", label: "Flag raised" },
  { value: "referral.create", label: "Referral created" },
  { value: "safeguarding.escalate", label: "Safeguarding escalation" },
];

const ACTION_LABELS = new Map(ACTIONS.map((action) => [action.value, action.label]));

function toneFor(action: string): "neutral" | "success" | "warning" | "danger" {
  if (action.startsWith("safeguarding")) return "danger";
  // Reads are access events, not state changes — they must not wear the
  // same warning colour as a role change or a stored credential.
  if (action.endsWith(".read") || action.endsWith(".list") || action.endsWith("_list"))
    return "neutral";
  if (action.startsWith("staff.") || action.startsWith("credential.")) return "warning";
  if (action.startsWith("flag.") || action.startsWith("referral.")) return "success";
  return "neutral";
}

export function AuditPanel() {
  const [data, setData] = useState<{ items: AuditEntry[]; total: number } | null>(null);
  const [chain, setChain] = useState<ChainStatus | null>(null);
  const [chainFailed, setChainFailed] = useState(false);
  const [page, setPage] = useState(1);
  const [action, setAction] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchAuditLog(page, action || undefined)
      .then((next) => {
        if (cancelled) return;
        setData(next);
        setError(null);
      })
      .catch((caught: unknown) => {
        if (cancelled) return;
        setData({ items: [], total: 0 });
        setError(caught instanceof Error ? caught.message : "The audit log could not be loaded.");
      });
    return () => {
      cancelled = true;
    };
  }, [page, action]);

  // Integrity is checked once per visit: it walks the whole chain, so it is
  // deliberately not re-run on every page change.
  useEffect(() => {
    let cancelled = false;
    fetchChainStatus()
      .then((next) => {
        if (!cancelled) setChain(next);
      })
      .catch(() => {
        if (!cancelled) setChainFailed(true);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const totalPages = data ? Math.max(1, Math.ceil(data.total / ADMIN_PAGE_SIZE)) : 1;

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatTile label="Entries" value={data?.total ?? "—"} hint="Matching the current filter" tone="pine" />
        <StatTile
          label="Chain"
          value={chain ? (chain.chain_intact ? "Intact" : "Broken") : chainFailed ? "Unknown" : "…"}
          hint={
            chain
              ? chain.chain_intact
                ? `${chain.entries_checked} entries verified`
                : `First break at sequence ${chain.first_broken_sequence}`
              : "Integrity check unavailable"
          }
          tone={chain ? (chain.chain_intact ? "pine" : "red") : "neutral"}
        />
        <StatTile label="Page" value={`${page} / ${totalPages}`} />
        <StatTile
          label="Retention"
          value="90d+"
          hint="Append-only; entries are never edited or removed"
        />
      </div>

      {chain && !chain.chain_intact && (
        <Alert tone="danger">
          Hash-chain verification fails from sequence {chain.first_broken_sequence}. Every
          entry from that point on is unproven — investigate before treating the
          log as evidence.
        </Alert>
      )}
      {error && <Alert tone="danger">{error}</Alert>}

      <section className="rounded-xl border border-line bg-surface">
        <header className="flex flex-wrap items-center gap-3 border-b border-line px-5 py-4">
          <div className="mr-auto">
            <h2 className="font-display text-lg font-semibold tracking-tight text-ink">
              Activity
            </h2>
            <p className="mt-1 text-xs text-ink-soft">
              Newest first. Resource identifiers are shown truncated — the log records
              what happened, not the contents of the record.
            </p>
          </div>
          <div className="w-full sm:w-56">
            <label htmlFor="audit-action" className="sr-only">
              Filter by action
            </label>
            <select
              id="audit-action"
              value={action}
              onChange={(event) => {
                setAction(event.target.value);
                setPage(1);
                setData(null);
              }}
              className="min-h-11 w-full rounded-lg border border-line bg-surface px-3 py-2 text-sm text-ink focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-pine"
            >
              {ACTIONS.map((option) => (
                <option key={option.value || "all"} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
        </header>

        <div className="py-2">
          {data === null ? (
            <div className="p-3">
              <SkeletonRows rows={8} />
            </div>
          ) : data.items.length === 0 ? (
            <div className="p-3">
              <EmptyState
                icon="audit"
                title="No entries for this filter"
                description="Switch back to All activity, or take an action elsewhere in the console — every admin action is recorded here."
              />
            </div>
          ) : (
            <TableScroll>
              <TableHead>
                <div className={`grid ${COLUMNS} gap-3`}>
                  <span>Seq</span>
                  <span>Action</span>
                  <span>Resource</span>
                  <span>When</span>
                </div>
              </TableHead>
              <ul>
                {data.items.map((entry) => (
                  <li key={entry.id}>
                    <TableRow className={COLUMNS}>
                      <span className="font-mono text-xs text-ink-soft">#{entry.sequence}</span>
                      <span>
                        <Badge tone={toneFor(entry.action)}>
                          {ACTION_LABELS.get(entry.action) ?? entry.action}
                        </Badge>
                      </span>
                      <span className="truncate text-xs text-ink-soft">
                        {entry.resource_type}
                        <span className="font-mono"> · {entry.resource_id.slice(0, 8)}…</span>
                      </span>
                      <span className="text-xs text-ink-soft">
                        {entry.timestamp.replace("T", " ").slice(0, 19)}
                      </span>
                    </TableRow>
                  </li>
                ))}
              </ul>
            </TableScroll>
          )}
        </div>

        <footer className="flex flex-wrap items-center gap-2 border-t border-line px-5 py-3">
          <Button variant="secondary" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
            Previous
          </Button>
          <span className="text-xs text-ink-soft">
            Page {page} of {totalPages}
          </span>
          <Button
            variant="secondary"
            disabled={page >= totalPages}
            onClick={() => setPage((p) => p + 1)}
          >
            Next
          </Button>
        </footer>
      </section>
    </div>
  );
}
