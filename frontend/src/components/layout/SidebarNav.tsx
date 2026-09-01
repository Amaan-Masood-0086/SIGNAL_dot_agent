"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

import { LogoutButton } from "@/src/components/features/auth/LogoutButton";
import { GrowthCurve } from "@/src/components/ui/GrowthCurve";
import { Icon } from "@/src/components/ui/Icon";
import { isActive, type NavGroup } from "@/src/components/layout/nav";

interface ShellUser {
  email: string | null;
  role: string;
  institutionName: string | null;
  isAdmin: boolean;
}

/**
 * The dashboard's persistent navigation: a fixed rail on desktop, a slide-in
 * drawer on mobile. `groups` arrives already filtered by role from the
 * server — this component never decides who may see what.
 */
export function SidebarNav({ groups, user }: { groups: NavGroup[]; user: ShellUser }) {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  // Escape closes the drawer; navigating closes it from the link's own
  // click handler below. (Closing from a pathname effect would fire a
  // cascading render on every route change, including on desktop where the
  // drawer state is irrelevant.)
  useEffect(() => {
    if (!open) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open]);

  return (
    <>
      {/* Mobile top bar — the only nav affordance below lg. */}
      <div className="flex items-center gap-3 border-b border-line bg-surface px-4 py-3 lg:hidden">
        <button
          type="button"
          onClick={() => setOpen(true)}
          aria-label="Open navigation"
          aria-expanded={open}
          className="inline-flex h-10 w-10 items-center justify-center rounded-lg border border-line text-ink-soft hover:bg-moss hover:text-ink focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-pine"
        >
          <Icon name="menu" />
        </button>
        <Link href="/dashboard" className="flex items-center gap-2" aria-label="SIGNAL dashboard">
          <GrowthCurve className="h-5 w-16 text-pine" />
          <span className="font-display text-base font-bold tracking-tight text-pine-deep">
            SIGNAL
          </span>
        </Link>
        {user.isAdmin && (
          <span className="ml-auto rounded-full bg-pine px-2.5 py-1 text-[10px] font-bold tracking-wide text-white uppercase">
            Admin
          </span>
        )}
      </div>

      {open && (
        <div
          className="fixed inset-0 z-40 bg-ink/40 lg:hidden"
          aria-hidden="true"
          onClick={() => setOpen(false)}
        />
      )}

      <nav
        aria-label="Dashboard"
        className={`fixed inset-y-0 left-0 z-50 flex w-72 flex-col border-r border-line bg-surface transition-transform duration-200 lg:sticky lg:top-0 lg:z-auto lg:h-svh lg:w-64 lg:translate-x-0 ${
          open ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex items-center gap-2.5 border-b border-line px-5 py-4">
          <Link
            href="/dashboard"
            className="flex items-center gap-2.5"
            aria-label="SIGNAL dashboard"
          >
            <GrowthCurve className="h-6 w-16 text-pine" />
            <span className="font-display text-lg font-bold tracking-tight text-pine-deep">
              SIGNAL
            </span>
          </Link>
          <button
            type="button"
            onClick={() => setOpen(false)}
            aria-label="Close navigation"
            className="ml-auto inline-flex h-9 w-9 items-center justify-center rounded-lg text-ink-soft hover:bg-moss hover:text-ink lg:hidden"
          >
            <Icon name="close" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-3 py-4">
          {groups.map((group) => (
            <div key={group.id} className="mb-5 last:mb-0">
              <p className="px-3 pb-2 text-[10px] font-bold tracking-[0.14em] text-ink-soft/80 uppercase">
                {group.label}
              </p>
              <ul className="space-y-0.5">
                {group.items.map((item) => {
                  const active = isActive(pathname, item);
                  return (
                    <li key={item.href}>
                      <Link
                        href={item.href}
                        onClick={() => setOpen(false)}
                        aria-current={active ? "page" : undefined}
                        className={`flex min-h-11 items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-pine ${
                          active
                            ? "bg-moss font-semibold text-pine-deep"
                            : "text-ink-soft hover:bg-moss/60 hover:text-ink"
                        }`}
                      >
                        <Icon
                          name={item.icon}
                          className={`h-5 w-5 shrink-0 ${active ? "text-pine" : "text-ink-soft/70"}`}
                        />
                        <span className="truncate">{item.label}</span>
                      </Link>
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}
        </div>

        <div className="border-t border-line px-5 py-4">
          <p className="text-[10px] font-bold tracking-[0.14em] text-ink-soft/80 uppercase">
            Signed in
          </p>
          <p className="mt-1.5 truncate text-sm font-semibold text-ink" title={user.email ?? undefined}>
            {user.email ?? "Synthetic staff account"}
          </p>
          <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
            <span
              className={`rounded-full px-2 py-0.5 text-[10px] font-bold tracking-wide uppercase ${
                user.isAdmin ? "bg-pine text-white" : "bg-moss text-pine-deep"
              }`}
            >
              {user.isAdmin ? "Admin" : user.role}
            </span>
            {user.institutionName && (
              <span className="truncate text-xs text-ink-soft" title={user.institutionName}>
                {user.institutionName}
              </span>
            )}
          </div>
          <div className="mt-3">
            <LogoutButton className="w-full" />
          </div>
        </div>
      </nav>
    </>
  );
}
