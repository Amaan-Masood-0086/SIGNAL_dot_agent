"use client";

import { useEffect, useMemo, useState } from "react";

import { Alert } from "@/src/components/ui/Alert";
import { Badge } from "@/src/components/ui/Badge";
import { Button } from "@/src/components/ui/Button";
import { EmptyState } from "@/src/components/ui/EmptyState";
import { Icon } from "@/src/components/ui/Icon";
import { SkeletonRows } from "@/src/components/ui/Skeleton";
import { StatTile } from "@/src/components/ui/StatTile";
import { TableHead, TableRow, TableScroll } from "@/src/components/ui/DataTable";
import { fetchAllChildren } from "@/src/lib/api/admin-client";
import { ADMIN_PAGE_SIZE, type AdminChild } from "@/src/lib/api/admin-schemas";

const COLUMNS = "grid-cols-[minmax(0,1.4fr)_minmax(0,1.2fr)_minmax(0,1fr)_7rem]";

/**
 * Read-only cross-institution oversight roster.
 *
 * There is deliberately no link through to a child profile here: the profile
 * route is institution-scoped on the backend and would 403 for a child
 * outside the admin's own institution. Oversight means counts and intake
 * status, not case access.
 */
export function AdminChildrenPanel() {
  const [data, setData] = useState<{ items: AdminChild[]; total: number } | null>(null);
  const [page, setPage] = useState(1);
  const [query, setQuery] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchAllChildren(page)
      .then((next) => {
        if (cancelled) return;
        setData(next);
        setError(null);
      })
      .catch((caught: unknown) => {
        if (cancelled) return;
        setData({ items: [], total: 0 });
        setError(caught instanceof Error ? caught.message : "The roster could not be loaded.");
      });
    return () => {
      cancelled = true;
    };
  }, [page]);

  const visible = useMemo(() => {
    const needle = query.trim().toLowerCase();
    if (!needle) return data?.items ?? [];
    return (data?.items ?? []).filter(
      (child) =>
        child.name.toLowerCase().includes(needle) ||
        child.institution_name.toLowerCase().includes(needle),
    );
  }, [data, query]);

  const items = data?.items ?? [];
  const estimated = items.filter((child) => !child.dob_confirmed).length;
  const institutions = new Set(items.map((child) => child.institution_id)).size;
  const totalPages = data ? Math.max(1, Math.ceil(data.total / ADMIN_PAGE_SIZE)) : 1;

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatTile label="Children" value={data?.total ?? "—"} hint="System-wide" tone="pine" />
        <StatTile label="Institutions" value={institutions} hint="Represented on this page" />
        <StatTile
          label="Estimated age"
          value={estimated}
          hint="On this page — confidence downgraded"
          tone={estimated > 0 ? "amber" : "neutral"}
        />
        <StatTile label="Page" value={`${page} / ${totalPages}`} />
      </div>

      {error && <Alert tone="danger">{error}</Alert>}

      <section className="rounded-xl border border-line bg-surface">
        <header className="flex flex-wrap items-center gap-3 border-b border-line px-5 py-4">
          <div className="mr-auto">
            <h2 className="font-display text-lg font-semibold tracking-tight text-ink">
              Oversight roster
            </h2>
            <p className="mt-1 text-xs text-ink-soft">
              Read-only. Caretaker surfaces remain strictly institution-scoped.
            </p>
          </div>
          <div className="relative w-full sm:w-64">
            <label htmlFor="admin-children-search" className="sr-only">
              Filter by child or institution
            </label>
            <Icon
              name="search"
              className="pointer-events-none absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2 text-ink-soft"
            />
            <input
              id="admin-children-search"
              type="search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Filter this page"
              maxLength={200}
              className="min-h-11 w-full rounded-lg border border-line bg-surface py-2 pr-3 pl-9 text-sm text-ink placeholder:text-ink-soft/60 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-pine"
            />
          </div>
        </header>

        <div className="py-2">
          {data === null ? (
            <div className="p-3">
              <SkeletonRows rows={6} />
            </div>
          ) : visible.length === 0 ? (
            <div className="p-3">
              <EmptyState
                icon="children"
                title={query ? "Nothing matches that filter" : "No children registered yet"}
                description={
                  query
                    ? "Clear the filter to see every child on this page."
                    : "Once caretakers register children, they appear here across every institution."
                }
              />
            </div>
          ) : (
            <TableScroll>
              <TableHead>
                <div className={`grid ${COLUMNS} gap-3`}>
                  <span>Child</span>
                  <span>Institution</span>
                  <span>Age basis</span>
                  <span>Intake</span>
                </div>
              </TableHead>
              <ul>
                {visible.map((child) => (
                  <li key={child.id}>
                    <TableRow className={COLUMNS}>
                      <span className="truncate font-semibold text-ink" title={child.name}>
                        {child.name}
                      </span>
                      <span className="truncate text-ink-soft" title={child.institution_name}>
                        {child.institution_name}
                      </span>
                      <span className="flex flex-wrap items-center gap-2">
                        <Badge tone={child.dob_confirmed ? "neutral" : "warning"}>
                          {child.dob_confirmed ? "Confirmed DOB" : "Estimated"}
                        </Badge>
                        <span className="text-xs text-ink-soft">
                          {child.dob_confirmed ? child.dob : child.estimated_age_range}
                        </span>
                      </span>
                      <span className="text-xs text-ink-soft">{child.intake_date}</span>
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
