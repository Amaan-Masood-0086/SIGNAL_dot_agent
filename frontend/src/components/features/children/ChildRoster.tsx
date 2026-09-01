"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import { Badge } from "@/src/components/ui/Badge";
import { EmptyState } from "@/src/components/ui/EmptyState";
import { Icon } from "@/src/components/ui/Icon";
import type { Child } from "@/src/lib/api/schemas";

// Filtering is purely client-side over the page the server already loaded —
// it never issues a request, so a caretaker typing a child's name can never
// leak that name into a URL, a log, or a query string.
export function ChildRoster({ items }: { items: Child[] }) {
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<"all" | "confirmed" | "estimated">("all");

  const visible = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return items.filter((child) => {
      if (filter === "confirmed" && !child.dob_confirmed) return false;
      if (filter === "estimated" && child.dob_confirmed) return false;
      return !needle || child.name.toLowerCase().includes(needle);
    });
  }, [items, query, filter]);

  const filters = [
    { id: "all", label: `All (${items.length})` },
    { id: "confirmed", label: "Confirmed DOB" },
    { id: "estimated", label: "Estimated age" },
  ] as const;

  return (
    <div>
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative min-w-0 flex-1 sm:max-w-xs">
          <label htmlFor="roster-search" className="sr-only">
            Search children by name
          </label>
          <Icon
            name="search"
            className="pointer-events-none absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2 text-ink-soft"
          />
          <input
            id="roster-search"
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search by name"
            maxLength={100}
            className="min-h-11 w-full rounded-lg border border-line bg-surface py-2 pr-3 pl-9 text-sm text-ink placeholder:text-ink-soft/60 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-pine"
          />
        </div>
        <div className="flex flex-wrap gap-1.5" role="group" aria-label="Filter roster">
          {filters.map((option) => (
            <button
              key={option.id}
              type="button"
              onClick={() => setFilter(option.id)}
              aria-pressed={filter === option.id}
              className={`min-h-9 rounded-full border px-3 py-1.5 text-xs font-semibold transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-pine ${
                filter === option.id
                  ? "border-pine bg-pine text-white"
                  : "border-line bg-surface text-ink-soft hover:border-pine/40 hover:text-ink"
              }`}
            >
              {option.label}
            </button>
          ))}
        </div>
      </div>

      {visible.length === 0 ? (
        <div className="mt-4">
          <EmptyState
            icon="search"
            title="No children match this view"
            description="Clear the search box or switch back to the All filter to see the full roster."
          />
        </div>
      ) : (
        <ul className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {visible.map((child) => (
            <li key={child.id}>
              <Link
                href={`/dashboard/children/${child.id}`}
                className="group flex h-full flex-col gap-3 rounded-xl border border-line bg-surface p-5 transition-colors duration-150 hover:border-pine/50 hover:bg-moss/40 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-pine"
                aria-label={`Open profile for ${child.name}`}
              >
                <div className="flex items-start justify-between gap-3">
                  <span className="font-display text-lg font-semibold tracking-tight text-ink group-hover:text-pine-deep">
                    {child.name}
                  </span>
                  <Badge tone={child.dob_confirmed ? "neutral" : "warning"}>
                    {child.dob_confirmed ? "Confirmed DOB" : "Estimated age"}
                  </Badge>
                </div>
                <div className="mt-auto flex items-end justify-between gap-2 text-xs text-ink-soft">
                  <span className="min-w-0">
                    {child.dob_confirmed
                      ? `Born ${child.dob}`
                      : `Age ${child.estimated_age_range ?? "—"}`}
                    <br />
                    Intake {child.intake_date}
                  </span>
                  <span
                    aria-hidden="true"
                    className="shrink-0 font-semibold text-pine transition-transform duration-150 group-hover:translate-x-0.5"
                  >
                    Open →
                  </span>
                </div>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
