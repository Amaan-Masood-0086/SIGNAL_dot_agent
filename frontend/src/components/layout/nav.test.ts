import { describe, expect, it } from "vitest";

import { NAV_GROUPS, isActive, navGroupsFor } from "./nav";

/**
 * The first frontend tests in this repo, and they cover the navigation
 * filter on purpose: it is the piece of UI logic with a security
 * consequence. A caretaker's HTML must not contain admin links, and the
 * system admin must not be offered a care surface that would file a child
 * under the wrong institution.
 *
 * The backend re-checks every admin endpoint against the DB staff row, so
 * nothing here grants access — but a regression that leaked admin links into
 * caretaker HTML would still be a real defect, and until now nothing caught it.
 */
describe("navGroupsFor", () => {
  it("gives a caretaker the care group and nothing else", () => {
    const groups = navGroupsFor(false);
    expect(groups.map((g) => g.id)).toEqual(["care"]);
  });

  it("gives the system admin the administration group and nothing else", () => {
    const groups = navGroupsFor(true);
    expect(groups.map((g) => g.id)).toEqual(["administration"]);
  });

  it("never exposes an admin href to a caretaker", () => {
    const hrefs = navGroupsFor(false).flatMap((g) => g.items.map((i) => i.href));
    expect(hrefs.every((href) => !href.startsWith("/dashboard/admin"))).toBe(true);
  });

  it("never offers the admin a child-registration surface", () => {
    // The admin role is system-level; a child registered by an admin would be
    // filed under the system tenant rather than a real institution.
    const hrefs = navGroupsFor(true).flatMap((g) => g.items.map((i) => i.href));
    expect(hrefs).not.toContain("/dashboard/children/new");
  });

  it("assigns every group to exactly one audience", () => {
    // A group that is both, or neither, would silently appear for the wrong
    // role the next time someone edits this file.
    for (const group of NAV_GROUPS) {
      const forCaretaker = !group.adminOnly;
      const forAdmin = !group.caretakerOnly;
      expect(
        forCaretaker !== forAdmin,
        `group "${group.id}" must belong to exactly one audience`,
      ).toBe(true);
    }
  });
});

describe("isActive", () => {
  const children = { href: "/dashboard", label: "Children", icon: "children", exact: true } as const;
  const providers = { href: "/dashboard/admin/providers", label: "P", icon: "key" } as const;

  it("matches an exact item only on the exact path", () => {
    expect(isActive("/dashboard", children)).toBe(true);
    // Without `exact`, the roster link would light up on every child page.
    expect(isActive("/dashboard/children/new", children)).toBe(false);
  });

  it("matches a prefix item on its sub-paths", () => {
    expect(isActive("/dashboard/admin/providers", providers)).toBe(true);
    expect(isActive("/dashboard/admin/staff", providers)).toBe(false);
  });
});
