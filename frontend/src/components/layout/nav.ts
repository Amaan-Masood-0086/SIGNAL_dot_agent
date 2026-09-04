import type { IconName } from "@/src/components/ui/Icon";

export interface NavItem {
  href: string;
  label: string;
  icon: IconName;
  /** Exact match only — otherwise a prefix match marks the parent active. */
  exact?: boolean;
}

export interface NavGroup {
  id: string;
  label: string;
  /** Groups marked admin-only are never rendered for a caretaker. */
  adminOnly?: boolean;
  /**
   * Groups marked caretaker-only are hidden from the system admin.
   *
   * The admin role is SYSTEM-level (NextaSol/dev), not a member of any
   * institution that delivers care. A child registered by an admin would be
   * filed under the admin's own institution rather than a real one — clean
   * data that is quietly wrong. Admins oversee care through "All children";
   * they do not deliver it.
   */
  caretakerOnly?: boolean;
  items: NavItem[];
}

// The single source of truth for dashboard navigation. RBAC lives in the
// data, not scattered across JSX: an admin-only group is filtered out on the
// server before the shell renders, so a caretaker's HTML never even contains
// a link to an admin route.
export const NAV_GROUPS: NavGroup[] = [
  {
    id: "care",
    label: "Care",
    caretakerOnly: true,
    items: [
      { href: "/dashboard", label: "Children", icon: "children", exact: true },
      { href: "/dashboard/children/new", label: "Register a child", icon: "add-child" },
    ],
  },
  {
    id: "administration",
    label: "Administration",
    adminOnly: true,
    items: [
      { href: "/dashboard/admin", label: "Overview", icon: "overview", exact: true },
      { href: "/dashboard/admin/providers", label: "Providers & keys", icon: "key" },
      { href: "/dashboard/admin/staff", label: "Staff & roles", icon: "staff" },
      { href: "/dashboard/admin/children", label: "All children", icon: "children" },
      { href: "/dashboard/admin/audit", label: "Audit log", icon: "audit" },
      { href: "/dashboard/admin/usage", label: "Usage & cost", icon: "usage" },
    ],
  },
];

export function navGroupsFor(isAdmin: boolean): NavGroup[] {
  return NAV_GROUPS.filter((group) =>
    isAdmin ? !group.caretakerOnly : !group.adminOnly,
  );
}

export function isActive(pathname: string, item: NavItem): boolean {
  return item.exact ? pathname === item.href : pathname.startsWith(item.href);
}
