"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { LogoutButton } from "@/src/components/features/auth/LogoutButton";
import { GrowthCurve } from "@/src/components/ui/GrowthCurve";
import { Icon } from "@/src/components/ui/Icon";
import { isActive, type NavGroup } from "@/src/components/layout/nav";

interface ShellUser { email: string | null; role: string; institutionName: string | null; isAdmin: boolean; }

export function SidebarNav({ groups, user }: { groups: NavGroup[]; user: ShellUser }) {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const dialog = useRef<HTMLDialogElement>(null);
  const trigger = useRef<HTMLButtonElement>(null);
  const home = user.isAdmin ? "/dashboard/admin" : "/dashboard";
  useEffect(() => {
    const node = dialog.current;
    const returnFocus = trigger.current;
    if (!node || !open) return;
    node.showModal();
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const media = window.matchMedia("(min-width: 1024px)");
    const closeOnDesktop = () => { if (media.matches) setOpen(false); };
    media.addEventListener("change", closeOnDesktop);
    return () => {
      node.close();
      document.body.style.overflow = previous;
      media.removeEventListener("change", closeOnDesktop);
      returnFocus?.focus();
    };
  }, [open]);
  function content(mobile = false) {
    return <div className="sidebar-inner">
      <div className="sidebar-brand">
        <Link href={home} onClick={() => setOpen(false)} className="flex items-center gap-3" aria-label="SIGNAL home">
          <span className="brand-mark"><GrowthCurve className="h-5 w-7" /></span>
          <span><span className="brand-name">SIGNAL</span><span className="brand-caption">Every observation matters</span></span>
        </Link>
        {mobile && <button className="ml-auto p-2" aria-label="Close navigation" onClick={() => setOpen(false)}><Icon name="close" /></button>}
      </div>
      <div className="sidebar-workspace"><Icon name={user.isAdmin ? "overview" : "children"} className="h-5 w-5 shrink-0 text-pine" /><div className="min-w-0"><strong title={user.institutionName ?? undefined}>{user.isAdmin ? "System workspace" : user.institutionName ?? "Care workspace"}</strong><small>{user.isAdmin ? "All institutions" : "Institution care team"}</small></div></div>
      <nav className="sidebar-links" aria-label="Dashboard">
        {groups.map(group => <div key={group.id}><p className="sidebar-label">{group.label}</p>{group.items.map(item => <Link key={item.href} href={item.href} className="nav-link" onClick={() => setOpen(false)} aria-current={isActive(pathname, item) ? "page" : undefined}><Icon name={item.icon} className="h-[18px] w-[18px] shrink-0" /><span>{item.label}</span></Link>)}</div>)}
      </nav>
      <div className="sidebar-note"><Link href="/dashboard/guide" onClick={() => setOpen(false)}>Workspace guide <Icon name="chevron-right" className="h-4 w-4" /></Link></div>
      <div className="sidebar-user"><div className="mb-3 flex items-center gap-3"><span className="initial-avatar" aria-hidden="true">{(user.email?.slice(0, 2) ?? "ST").toUpperCase()}</span><div className="min-w-0"><p className="truncate text-xs font-semibold" title={user.email ?? undefined}>{user.email ?? "Staff account"}</p><p className="mt-1 text-xs text-ink-soft">{user.isAdmin ? "System administrator" : "Caretaker"}</p></div></div><LogoutButton className="w-full" /></div>
    </div>;
  }
  return <>
    <aside className="sidebar">{content()}</aside>
    <div className="mobile-bar"><Link href={home} className="brand-name">SIGNAL</Link><button ref={trigger} type="button" onClick={() => setOpen(true)} aria-label="Open navigation" aria-expanded={open} aria-controls="mobile-navigation" className="rounded-lg border border-line p-2.5"><Icon name="menu" /></button></div>
    <dialog ref={dialog} id="mobile-navigation" className="mobile-nav-dialog" aria-label="Workspace navigation" onCancel={() => setOpen(false)} onClick={event => { if (event.target === event.currentTarget) setOpen(false); }}>{open && content(true)}</dialog>
  </>;
}
