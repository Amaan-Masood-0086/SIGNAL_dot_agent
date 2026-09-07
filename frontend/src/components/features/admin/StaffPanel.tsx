"use client";

import { useEffect, useMemo, useState } from "react";

import { Alert } from "@/src/components/ui/Alert";
import { Badge } from "@/src/components/ui/Badge";
import { Button } from "@/src/components/ui/Button";
import { ConfirmDialog } from "@/src/components/ui/ConfirmDialog";
import { EmptyState } from "@/src/components/ui/EmptyState";
import { Icon } from "@/src/components/ui/Icon";
import { SkeletonRows } from "@/src/components/ui/Skeleton";
import { StatTile } from "@/src/components/ui/StatTile";
import { TableHead, TableRow, TableScroll } from "@/src/components/ui/DataTable";
import { AddStaffForm } from "@/src/components/features/admin/AddStaffForm";
import { deleteStaff, fetchStaff, updateStaffActive, updateStaffRole } from "@/src/lib/api/admin-client";
import { ADMIN_PAGE_SIZE, type AdminStaff } from "@/src/lib/api/admin-schemas";

const COLUMNS = "grid-cols-[minmax(0,2fr)_7rem_6rem_minmax(0,13rem)]";

type PendingAction =
  | { kind: "role"; staff: AdminStaff; nextRole: "admin" | "caretaker" }
  | { kind: "active"; staff: AdminStaff; nextActive: boolean }
  | { kind: "delete"; staff: AdminStaff };

/**
 * Staff directory + the only promotion path in the product.
 *
 * `currentStaffId` is used solely to disable self-targeting controls: the
 * backend refuses self-demotion and self-deactivation outright (the rail
 * that stops an admin locking everyone out), so offering those buttons would
 * only produce a guaranteed 409.
 */
export function StaffPanel({ currentStaffId }: { currentStaffId: string }) {
  const [data, setData] = useState<{ items: AdminStaff[]; total: number } | null>(null);
  const [page, setPage] = useState(1);
  const [query, setQuery] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [pending, setPending] = useState<PendingAction | null>(null);
  const [working, setWorking] = useState(false);

  const [reloadKey, setReloadKey] = useState(0);

  // State is set only from a resolved promise, and a response that lands
  // after the operator has already paged away is discarded.
  useEffect(() => {
    let cancelled = false;
    fetchStaff(page)
      .then((next) => {
        if (cancelled) return;
        setData(next);
        setError(null);
      })
      .catch((caught: unknown) => {
        if (cancelled) return;
        setData({ items: [], total: 0 });
        setError(caught instanceof Error ? caught.message : "Staff could not be loaded.");
      });
    return () => {
      cancelled = true;
    };
  }, [page, reloadKey]);

  const visible = useMemo(() => {
    const needle = query.trim().toLowerCase();
    if (!needle) return data?.items ?? [];
    return (data?.items ?? []).filter((staff) => staff.email.toLowerCase().includes(needle));
  }, [data, query]);

  const admins = (data?.items ?? []).filter((staff) => staff.role === "admin" && staff.is_active);
  const deactivated = (data?.items ?? []).filter((staff) => !staff.is_active);

  async function commit() {
    if (!pending || working) return;
    setWorking(true);
    setNotice(null);
    setError(null);
    try {
      if (pending.kind === "role") {
        await updateStaffRole(pending.staff.id, pending.nextRole);
        setNotice(`${pending.staff.email} is now a ${pending.nextRole}.`);
      } else if (pending.kind === "delete") {
        await deleteStaff(pending.staff.id);
        setNotice(`${pending.staff.email} was permanently deleted.`);
      } else {
        await updateStaffActive(pending.staff.id, pending.nextActive);
        setNotice(
          pending.nextActive
            ? `${pending.staff.email} was reactivated.`
            : `${pending.staff.email} was deactivated and can no longer sign in.`,
        );
      }
      setPending(null);
      setReloadKey((key) => key + 1);
    } catch (caught) {
      setPending(null);
      setError(caught instanceof Error ? caught.message : "The change could not be applied.");
    } finally {
      setWorking(false);
    }
  }

  const totalPages = data ? Math.max(1, Math.ceil(data.total / ADMIN_PAGE_SIZE)) : 1;

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatTile label="Staff accounts" value={data?.total ?? "—"} tone="pine" />
        <StatTile label="Active admins" value={admins.length} hint="On this page" />
        <StatTile
          label="Deactivated"
          value={deactivated.length}
          hint="On this page"
          tone={deactivated.length > 0 ? "amber" : "neutral"}
        />
        <StatTile label="Page" value={`${page} / ${totalPages}`} />
      </div>

      {notice && <Alert tone="success">{notice}</Alert>}
      {error && <Alert tone="danger">{error}</Alert>}

      {/* The only way to onboard anyone through the product. Before this
          existed the sole paths were two seed scripts run by someone with
          database access. */}
      <AddStaffForm onCreated={() => setReloadKey((key) => key + 1)} />

      <section className="rounded-xl border border-line bg-surface">
        <header className="flex flex-wrap items-center gap-3 border-b border-line px-5 py-4">
          <h2 className="mr-auto font-display text-lg font-semibold tracking-tight text-ink">
            Directory
          </h2>
          <div className="relative w-full sm:w-64">
            <label htmlFor="staff-search" className="sr-only">
              Filter staff by email
            </label>
            <Icon
              name="search"
              className="pointer-events-none absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2 text-ink-soft"
            />
            <input
              id="staff-search"
              type="search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Filter this page by email"
              maxLength={320}
              className="min-h-11 w-full rounded-lg border border-line bg-surface py-2 pr-3 pl-9 text-sm text-ink placeholder:text-ink-soft/60 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-pine"
            />
          </div>
        </header>

        <div className="py-2">
          {data === null ? (
            <div className="p-3">
              <SkeletonRows rows={5} />
            </div>
          ) : visible.length === 0 ? (
            <div className="p-3">
              <EmptyState
                icon="staff"
                title={query ? "No staff match that filter" : "No staff accounts yet"}
                description={
                  query
                    ? "Clear the filter to see everyone on this page."
                    : "Staff accounts are created by the seeding script; roles are then managed here."
                }
              />
            </div>
          ) : (
            <TableScroll>
              <TableHead>
                <div className={`grid ${COLUMNS} gap-3`}>
                  <span>Account</span>
                  <span>Role</span>
                  <span>Status</span>
                  <span className="text-right">Actions</span>
                </div>
              </TableHead>
              <ul>
                {visible.map((staff) => {
                  const isSelf = staff.id === currentStaffId;
                  return (
                    <li key={staff.id}>
                      <TableRow className={COLUMNS}>
                        <div className="min-w-0">
                          <p className="truncate font-semibold text-ink" title={staff.email}>
                            {staff.email}
                            {isSelf && (
                              <span className="ml-2 text-[10px] font-bold tracking-wide text-pine uppercase">
                                You
                              </span>
                            )}
                          </p>
                          <p className="text-xs text-ink-soft">
                            Since {staff.created_at.slice(0, 10)}
                          </p>
                        </div>
                        <div>
                          <Badge tone={staff.role === "admin" ? "success" : "neutral"}>
                            {staff.role}
                          </Badge>
                        </div>
                        <div>
                          <Badge tone={staff.is_active ? "neutral" : "warning"}>
                            {staff.is_active ? "active" : "deactivated"}
                          </Badge>
                        </div>
                        <div className="flex flex-wrap justify-end gap-2">
                          {isSelf ? (
                            <span className="text-xs text-ink-soft">
                              Another admin must change your own account
                            </span>
                          ) : (
                            <>
                              <Button
                                variant="secondary"
                                onClick={() =>
                                  setPending({
                                    kind: "role",
                                    staff,
                                    nextRole: staff.role === "admin" ? "caretaker" : "admin",
                                  })
                                }
                              >
                                {staff.role === "admin" ? "Demote" : "Promote"}
                              </Button>
                              <Button
                                variant="ghost"
                                onClick={() =>
                                  setPending({
                                    kind: "active",
                                    staff,
                                    nextActive: !staff.is_active,
                                  })
                                }
                                className={staff.is_active ? "text-red hover:bg-red-soft hover:text-red" : ""}
                              >
                                {staff.is_active ? "Deactivate" : "Reactivate"}
                              </Button>
                              {/* Deletion succeeds only for an account that
                                  never did anything. The backend refuses once
                                  the audit chain names it as an actor, and
                                  says so — this button surfaces that answer
                                  rather than pretending to predict it. */}
                              <Button
                                variant="ghost"
                                onClick={() => setPending({ kind: "delete", staff })}
                                aria-label={`Delete ${staff.email}`}
                                className="text-red hover:bg-red-soft hover:text-red"
                              >
                                Delete
                              </Button>
                            </>
                          )}
                        </div>
                      </TableRow>
                    </li>
                  );
                })}
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
        title={
          pending?.kind === "delete"
            ? "Delete this account permanently?"
            : pending?.kind === "role"
            ? pending.nextRole === "admin"
              ? "Grant system-level admin?"
              : "Remove admin access?"
            : pending?.nextActive
              ? "Reactivate this account?"
              : "Deactivate this account?"
        }
        description={
          pending?.kind === "delete" ? (
            <>
              <span className="font-semibold text-ink">{pending.staff.email}</span>{" "}
              will be removed from the database entirely. This cannot be undone.
              <span className="mt-3 block">
                It only works for an account that never did anything. If this
                person has run screening sessions the audit trail names them as
                the actor behind those findings, and the request will be refused
                with a note to deactivate instead — which removes their access
                and keeps the attribution.
              </span>
            </>
          ) : pending?.kind === "role" ? (
            pending.nextRole === "admin" ? (
              <>
                <span className="font-semibold text-ink">{pending.staff.email}</span> will be able
                to see children and staff across every institution, manage provider
                credentials, and read the audit log. This takes effect immediately —
                not when their current session expires.
              </>
            ) : (
              <>
                <span className="font-semibold text-ink">{pending.staff.email}</span> loses admin
                access immediately and keeps caretaker access to their own
                institution only.
              </>
            )
          ) : pending?.nextActive ? (
            <>
              <span className="font-semibold text-ink">{pending.staff.email}</span> will be able to
              sign in again with their previous role.
            </>
          ) : (
            <>
              <span className="font-semibold text-ink">{pending?.staff.email}</span> will be blocked
              at the next sign-in and can create nothing new. The account is
              deactivated, never deleted — the audit trail stays intact.
            </>
          )
        }
        confirmLabel={
          pending?.kind === "delete"
            ? "Delete permanently"
            : pending?.kind === "role"
            ? pending.nextRole === "admin"
              ? "Grant admin"
              : "Remove admin"
            : pending?.nextActive
              ? "Reactivate"
              : "Deactivate"
        }
        tone={
          pending?.kind === "active" && !pending.nextActive
            ? "danger"
            : pending?.kind === "role" && pending.nextRole === "admin"
              ? "danger"
              : "primary"
        }
        pending={working}
        onConfirm={commit}
        onCancel={() => setPending(null)}
      />
    </div>
  );
}
