"use client";
import Link from "next/link";
import { useMemo, useState } from "react";
import { Badge } from "@/src/components/ui/Badge";
import { EmptyState } from "@/src/components/ui/EmptyState";
import { Icon } from "@/src/components/ui/Icon";
import type { Child } from "@/src/lib/api/schemas";

export function ChildRoster({ items, archived = [], total = items.length, archivedTotal = archived.length, archivedUnavailable = false }: {
  items: Child[]; archived?: Child[]; total?: number; archivedTotal?: number; archivedUnavailable?: boolean;
}) {
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<"all" | "confirmed" | "estimated" | "archived">("all");
  const [sort, setSort] = useState("name");
  const source = filter === "archived" ? archived : items;
  const visible = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return source.filter(child => (filter !== "confirmed" || child.dob_confirmed) && (filter !== "estimated" || !child.dob_confirmed) && (!needle || child.name.toLowerCase().includes(needle))).sort((a, b) => sort === "recent" ? b.intake_date.localeCompare(a.intake_date) : a.name.localeCompare(b.name));
  }, [source, query, filter, sort]);
  const filters = [{ id: "all", label: "Active children", count: items.length }, { id: "confirmed", label: "Confirmed DOB" }, { id: "estimated", label: "Estimated age" }, { id: "archived", label: "Archived", count: archivedUnavailable ? undefined : archived.length }] as const;
  const sourceTotal = filter === "archived" ? archivedTotal : total;
  return <section className="roster-panel" aria-label="Children directory">
    <div className="roster-toolbar"><div><h2 className="font-display text-lg font-semibold">Your children</h2><p className="mt-1 text-xs text-ink-soft">Open a profile to record an observation or review its history.</p></div>
      <div className="flex w-full gap-2 sm:w-auto"><div className="relative min-w-0 flex-1"><label htmlFor="roster-search" className="sr-only">Search children by name</label><Icon name="search" className="pointer-events-none absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2 text-ink-soft" /><input id="roster-search" type="search" value={query} onChange={e => setQuery(e.target.value)} placeholder="Search children" maxLength={100} className="min-h-11 w-full rounded-lg border border-line bg-paper py-2 pr-3 pl-9 text-xs sm:w-52" /></div><label className="sr-only" htmlFor="roster-sort">Sort children</label><select id="roster-sort" value={sort} onChange={e => setSort(e.target.value)} className="min-h-11 rounded-lg border border-line bg-surface px-2 text-xs"><option value="name">Name A–Z</option><option value="recent">Newest intake</option></select></div>
    </div>
    <div className="roster-tabs" role="group" aria-label="Filter roster">{filters.map(option => <button key={option.id} type="button" onClick={() => setFilter(option.id)} aria-pressed={filter === option.id} className="roster-tab">{option.label}{"count" in option && option.count !== undefined && <span className="ml-1.5 rounded bg-paper px-1.5 py-0.5 text-xs">{option.count}</span>}</button>)}</div>
    {filter === "archived" && archivedUnavailable ? <div className="p-6" role="alert">Archived records could not be loaded. Refresh to try again.</div> : visible.length === 0 ? <div className="p-6"><EmptyState icon="search" title={query ? "No matching children" : filter === "archived" ? "No archived children" : "No children in this view"} description={query ? "Try a different name or clear the search to see this list." : "Switch to Active children to return to the current roster."} /></div> : <>
      <div className="roster-columns" aria-hidden="true"><span>Child</span><span>Age information</span><span>Registered</span><span>Record status</span><span /></div>
      <ul>{visible.map(child => <li key={child.id}><Link href={`/dashboard/children/${child.id}`} className="roster-row">
        <div className="flex min-w-0 items-center gap-3"><span className="initial-avatar" aria-hidden="true">{child.name.split(/\s+/).slice(0, 2).map(n => n[0]).join("").toUpperCase()}</span><div className="min-w-0"><strong className="block truncate">{child.name}</strong><small>Child profile</small></div></div>
        <div className="roster-age">{child.dob_confirmed ? child.dob : child.estimated_age_range ?? "Not recorded"}<small>{child.dob_confirmed ? "Date of birth" : "Recorded estimate"}</small></div>
        <span className="roster-intake text-ink-soft">{child.intake_date}</span><div className="roster-status"><Badge tone={child.archived_at || !child.dob_confirmed ? "warning" : "neutral"}>{child.archived_at ? "Archived" : child.dob_confirmed ? "Confirmed DOB" : "Estimated age"}</Badge></div><Icon name="chevron-right" className="h-4 w-4 text-ink-soft" />
      </Link></li>)}</ul>
    </>}
    <footer className="roster-footer" role="status">{visible.length} {visible.length === 1 ? "child" : "children"} shown{source.length < sourceTotal ? ` · Search covers ${source.length} loaded records of ${sourceTotal}` : ""}. Records stay within your institution.</footer>
  </section>;
}
