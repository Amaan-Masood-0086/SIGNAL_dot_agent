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
import { AddChildForm } from "@/src/components/features/admin/AddChildForm";
import {
  archiveChild,
  assignChild,
  deleteChild,
  fetchAllChildren,
  fetchStaff,
  restoreChild,
} from "@/src/lib/api/admin-client";
import { ConfirmDialog } from "@/src/components/ui/ConfirmDialog";
import { Input } from "@/src/components/ui/Input";
import { ADMIN_PAGE_SIZE, type AdminChild, type AdminStaff } from "@/src/lib/api/admin-schemas";

const COLUMNS =
  "grid-cols-[minmax(0,1.2fr)_minmax(0,1fr)_minmax(0,0.9fr)_minmax(0,1.1fr)_minmax(0,12rem)]";

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
  // Bumped after a registration so the roster reflects it without a manual
  // refresh; the cancellation guard below still discards a stale response.
  const [reloadKey, setReloadKey] = useState(0);
  const [staff, setStaff] = useState<AdminStaff[]>([]);
  const [notice, setNotice] = useState<string | null>(null);
  const [working, setWorking] = useState(false);
  const [pending, setPending] = useState<
    { kind: "delete" | "archive"; child: AdminChild } | null
  >(null);
  const [reason, setReason] = useState("");

  // The assignment picker needs names, not ids. Loaded once alongside the
  // roster rather than per row.
  useEffect(() => {
    let cancelled = false;
    fetchStaff(1)
      .then((next) => {
        if (!cancelled) setStaff(next.items.filter((s) => s.is_active));
      })
      .catch(() => {
        if (!cancelled) setStaff([]);
      });
    return () => {
      cancelled = true;
    };
  }, [reloadKey]);

  async function act(run: () => Promise<unknown>, done: string) {
    if (working) return;
    setWorking(true);
    setNotice(null);
    setError(null);
    try {
      await run();
      setNotice(done);
      setPending(null);
      setReason("");
      setReloadKey((k) => k + 1);
    } catch (caught) {
      // The backend's refusal carries the reason AND the safe alternative;
      // it reaches the operator verbatim rather than as "Request failed".
      setError(caught instanceof Error ? caught.message : "That did not work.");
      setPending(null);
    } finally {
      setWorking(false);
    }
  }

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
  }, [page, reloadKey]);

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

      {notice && <Alert tone="success">{notice}</Alert>}
      {error && <Alert tone="danger">{error}</Alert>}

      {/* Registration takes an EXPLICIT institution. The caretaker form
          derives one from the token, which a system-level admin does not
          have — filing a real child under the system tenant is the failure
          the caretaker-only nav guard exists to prevent. */}
      <AddChildForm onCreated={() => setReloadKey((key) => key + 1)} />

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
                  <span>Assigned to</span>
                  <span className="text-right">Actions</span>
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
                      <span>
                        {/* Responsibility, not access: assigning does NOT
                            hide the child from anyone else at the
                            institution. Narrowing visibility is a separate
                            decision (backlog R8). */}
                        <label className="sr-only" htmlFor={`assign-${child.id}`}>
                          Assign {child.name} to a staff member
                        </label>
                        <select
                          id={`assign-${child.id}`}
                          value={child.assigned_staff_id ?? ""}
                          disabled={working}
                          onChange={(event) =>
                            void act(
                              () => assignChild(child.id, event.target.value || null),
                              event.target.value
                                ? `${child.name} assigned.`
                                : `${child.name} is now unassigned.`,
                            )
                          }
                          className="min-h-9 w-full rounded-lg border border-line bg-surface px-2 py-1 text-xs text-ink focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-pine disabled:opacity-60"
                        >
                          <option value="">Unassigned</option>
                          {staff
                            .filter((s) => s.institution_id === child.institution_id)
                            .map((s) => (
                              <option key={s.id} value={s.id}>
                                {s.email}
                              </option>
                            ))}
                        </select>
                      </span>
                      <span className="flex flex-wrap justify-end gap-1.5">
                        {child.archived_at ? (
                          <Button
                            variant="secondary"
                            disabled={working}
                            onClick={() =>
                              void act(
                                () => restoreChild(child.id),
                                `${child.name} is back on the roster.`,
                              )
                            }
                            aria-label={`Restore ${child.name}`}
                          >
                            Restore
                          </Button>
                        ) : (
                          <Button
                            variant="secondary"
                            disabled={working}
                            onClick={() => setPending({ kind: "archive", child })}
                            aria-label={`Archive ${child.name}`}
                          >
                            Archive
                          </Button>
                        )}
                        <Button
                          variant="ghost"
                          disabled={working}
                          onClick={() => setPending({ kind: "delete", child })}
                          aria-label={`Delete ${child.name}`}
                          className="text-red hover:bg-red-soft hover:text-red"
                        >
                          Delete
                        </Button>
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
      <ConfirmDialog
        open={pending !== null}
        interactive={pending?.kind === "archive"}
        title={
          pending?.kind === "delete"
            ? "Delete this child permanently?"
            : `Archive ${pending?.child.name ?? "this child"}?`
        }
        description={
          pending?.kind === "delete" ? (
            <>
              <span className="font-semibold text-ink">{pending.child.name}</span>{" "}
              will be removed from the database entirely. This cannot be undone.
              <span className="mt-3 block">
                It only works for a record with no screening history. If any
                session, observation or flag exists, the request is refused —
                deleting it would destroy clinical evidence, and archiving is
                the right removal for that case.
              </span>
            </>
          ) : (
            <>
              <span className="block">
                They come off the roster. Nothing is deleted: the profile, the
                sessions and every screening result stay exactly as they are,
                and this can be undone at any time.
              </span>
              <span className="mt-3 block">
                <Input
                  id="admin-archive-reason"
                  label="Reason"
                  autoFocus
                  value={reason}
                  maxLength={200}
                  onChange={(event) => setReason(event.target.value)}
                  placeholder="e.g. Duplicate registration, or left the institution"
                  hint="Recorded in the audit log — a later reviewer needs to know why."
                />
              </span>
            </>
          )
        }
        confirmLabel={pending?.kind === "delete" ? "Delete permanently" : "Archive"}
        tone="danger"
        pending={working}
        onConfirm={() => {
          if (!pending) return;
          if (pending.kind === "delete") {
            void act(
              () => deleteChild(pending.child.id),
              `${pending.child.name} was permanently deleted.`,
            );
          } else if (reason.trim().length >= 3) {
            void act(
              () => archiveChild(pending.child.id, reason.trim()),
              `${pending.child.name} was archived.`,
            );
          }
        }}
        onCancel={() => {
          setPending(null);
          setReason("");
        }}
      />
    </div>
  );
}
