import { readFileSync } from "node:fs";
import path from "node:path";
import { expect, test, type Page } from "@playwright/test";

// WCAG 2.0 to 2.2 AA scan with axe-core on the real pages against the
// synthetic fixture API. Evaluated through CDP, so the per-request CSP nonce
// does not block it.
const axeSource = readFileSync(path.join(process.cwd(), "node_modules/axe-core/axe.min.js"), "utf8");
const WIDTHS = [360, 1440];
const CARETAKER = ["/dashboard", "/dashboard/children/new", "/dashboard/referrals", "/dashboard/guide"];
const ADMIN = ["/dashboard/admin", "/dashboard/admin/staff", "/dashboard/admin/children", "/dashboard/admin/providers", "/dashboard/admin/audit", "/dashboard/admin/usage"];

async function login(page: Page, role: "caretaker" | "admin") {
  await page.goto("/login");
  await page.getByLabel("Email", { exact: true }).fill(`${role}@fixture.test`);
  await page.getByLabel("Password", { exact: true }).fill("synthetic-test-only");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page.getByRole("heading", { name: role === "admin" ? "System overview" : "Care overview" })).toBeVisible();
}

async function scan(page: Page, route: string, width: number) {
  await page.setViewportSize({ width, height: 900 });
  await page.goto(route);
  await expect(page.locator("main")).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), `${route} overflows at ${width}px`).toBe(true);
  await page.evaluate(axeSource);
  const violations = await page.evaluate(async () => {
    // @ts-expect-error axe is injected into the page above
    const result = await axe.run(document, { runOnly: { type: "tag", values: ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"] } });
    return result.violations.map((v: { id: string; help: string; nodes: { target: string[] }[] }) => `${v.id}: ${v.help} (${v.nodes[0].target.join(" ")})`);
  });
  expect(violations, `${route} at ${width}px`).toEqual([]);
}

test("caretaker pages have no axe violations at phone and desktop widths", async ({ page }) => {
  await login(page, "caretaker");
  for (const width of WIDTHS) for (const route of CARETAKER) await scan(page, route, width);
});

test("administrator pages have no axe violations at phone and desktop widths", async ({ page }) => {
  await login(page, "admin");
  for (const width of WIDTHS) for (const route of ADMIN) await scan(page, route, width);
});
