import { expect, test, type Page } from "@playwright/test";

async function login(page: Page, role = "caretaker") {
  await page.goto("/login");
  await page.getByLabel("Email", { exact: true }).fill(`${role}@fixture.test`);
  await page.getByLabel("Password", { exact: true }).fill("synthetic-test-only");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page.getByRole("heading", { name: role === "admin" ? "System overview" : "Care overview" })).toBeVisible();
}
async function fits(page: Page) {
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
}

test("caretaker directory, search, profile and saved observation", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  await login(page);
  await expect(page.getByRole("link", { name: "Staff & roles" })).toHaveCount(0);
  await page.screenshot({ path: "test-results/caretaker-desktop.png", fullPage: true, caret: "initial" });
  await page.getByLabel("Search children by name").fill("no-such-child");
  await expect(page.getByText("No matching children")).toBeVisible();
  await page.getByLabel("Search children by name").fill("Amina");
  await page.getByRole("link", { name: /Test Amina/ }).click();
  await expect(page.getByRole("heading", { name: "Test Amina" })).toBeVisible();
  await page.screenshot({ path: "test-results/child-profile.png", fullPage: true, caret: "initial" });
  await page.getByRole("button", { name: "Start a text observation session" }).click();
  await expect(page.getByRole("heading", { name: "Chat with SIGNAL", exact: true })).toBeVisible();
  await expect(page.getByRole("log", { name: "Conversation messages" })).toBeVisible();
  await page.screenshot({ path: "test-results/chat-new-desktop.png", fullPage: true });
  await page.setViewportSize({ width: 390, height: 844 });
  await fits(page);
  await page.screenshot({ path: "test-results/chat-new-mobile.png", fullPage: true });
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.getByLabel("What did you notice?").fill("Synthetic observation for interface testing.");
  await expect(page.getByRole("button", { name: "Complete this observation session" })).toBeDisabled();
  await page.getByRole("button", { name: "Save this turn without screening it" }).click();
  await expect(page.getByLabel("What did you notice?")).toHaveValue("");
  await expect(page.getByText("Synthetic observation for interface testing.", { exact: true })).toBeVisible();
  await page.screenshot({ path: "test-results/session-desktop.png", fullPage: true, caret: "initial" });
  await page.reload();
  await expect(page.getByText("Synthetic observation for interface testing.", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Complete this observation session" }).click();
  await expect(page.getByText("Completed", { exact: true })).toBeVisible();
  await fits(page);
});

test("saved screening result and original evidence survive reload without another screening", async ({ page }) => {
  await login(page);
  await page.getByRole("link", { name: /Test Amina/ }).click();
  await page.getByRole("button", { name: "Start a text observation session" }).click();
  await page.getByLabel("What did you notice?").fill("Synthetic screening recovery observation.");
  await page.getByRole("button", { name: "Send observation to SIGNAL" }).click();
  await expect(page.getByText("Synthetic saved explanation for recovery testing.")).toBeVisible();
  let screeningCalls = 0;
  page.on("request", request => { if (request.url().endsWith("/reason")) screeningCalls++; });
  await page.reload();
  const saved = page.getByRole("region", { name: "Saved screening results" });
  await expect(saved).toBeVisible();
  await expect(saved.getByText("Synthetic saved explanation for recovery testing.")).toBeVisible();
  await expect(saved.getByText("Original synthetic evidence wording.")).toBeVisible();
  await expect(saved.getByText(/has been revised since this result/)).toBeVisible();
  await expect(page.getByRole("button", { name: "Send observation to SIGNAL" })).toHaveCount(0);
  expect(screeningCalls).toBe(0);
  await saved.getByRole("link", { name: "Referral & follow-up" }).click();
  await expect(page.getByRole("heading", { name: "Confirm a referral" })).toBeVisible();
  await page.getByLabel("Responsible person").fill("Synthetic follow-up owner");
  await page.getByLabel("Review date").fill("2020-01-01");
  await page.getByRole("button", { name: "Confirm referral" }).click();
  await expect(page.getByRole("checkbox")).toBeFocused();
  await page.getByRole("checkbox").check();
  await page.getByRole("button", { name: "Confirm referral" }).click();
  await expect(page.getByRole("heading", { name: "Referral follow-up" })).toBeVisible();
  await expect(page.getByText(/This referral is overdue/)).toBeVisible();
  await page.getByLabel("Follow-up status").selectOption("pending_capacity");
  await page.getByRole("button", { name: "Save follow-up" }).click();
  await expect(page.getByRole("status")).toContainText("Follow-up record saved");
  await page.reload();
  await expect(page.getByLabel("Follow-up status")).toHaveValue("pending_capacity");
  await page.setViewportSize({ width: 390, height: 844 });
  await fits(page);
  await page.screenshot({ path: "test-results/referral-mobile.png", caret: "initial", fullPage: true });
  await page.getByLabel("Follow-up status").selectOption("closed");
  await page.getByRole("button", { name: "Save follow-up" }).click();
  await expect(page.getByRole("status")).toContainText("Follow-up record saved");
  await page.reload();
  await expect(page.getByLabel("Follow-up status")).toHaveValue("closed");
  await page.getByRole("link", { name: "Back to referral queue" }).click();
  await expect(page.getByRole("link", { name: "Synthetic follow-up owner" })).toBeVisible();
});

test("mobile navigation traps focus, filters and role refusal work", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await login(page);
  await fits(page);
  await page.screenshot({ path: "test-results/caretaker-mobile.png", fullPage: true, caret: "initial" });
  await page.getByRole("button", { name: "Open navigation" }).click();
  const dialog = page.getByRole("dialog", { name: "Workspace navigation" });
  await expect(dialog).toBeVisible();
  for (let i = 0; i < 12; i++) await page.keyboard.press("Tab");
  expect(await page.evaluate(() => !!document.activeElement?.closest("dialog"))).toBe(true);
  await page.keyboard.press("Escape");
  await expect(dialog).not.toBeVisible();
  await expect(page.getByRole("button", { name: "Open navigation" })).toBeFocused();
  await page.getByRole("button", { name: "Estimated age", exact: true }).click();
  await expect(page.getByRole("link", { name: /Test Amina/ })).toHaveCount(0);
  await page.goto("/dashboard/admin");
  await expect(page.getByRole("heading", { name: "Admin access required" })).toBeVisible();
  await fits(page);
});

test("age mode can change after typing and registration succeeds", async ({ page }) => {
  await login(page);
  await page.getByRole("link", { name: "Register a child", exact: true }).first().click();
  await page.getByLabel("Child name or identifier").fill("Test New Record");
  await page.getByLabel("Confirmed date of birth", { exact: true }).fill("2023-01-02");
  await page.getByRole("radio", { name: "Age is estimated", exact: false }).check();
  await page.getByLabel("Estimated age range", { exact: true }).fill("30-36 months");
  await page.screenshot({ path: "test-results/intake.png", fullPage: true, caret: "initial" });
  await page.getByRole("button", { name: "Register child", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Registration complete" })).toBeVisible();
});

test("administrator surfaces are reachable and cost absence is explicit", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  await login(page, "admin");
  await expect(page.getByRole("link", { name: "Register a child", exact: true })).toHaveCount(0);
  await expect(page.getByText("Not recorded", { exact: true })).toBeVisible();
  await page.screenshot({ path: "test-results/admin-desktop.png", fullPage: true, caret: "initial" });
  await page.goto("/dashboard/admin/staff");
  await page.getByRole("button", { name: "Promote", exact: true }).click();
  const confirmation = page.getByRole("alertdialog", { name: "Grant system-level admin?" });
  await expect(confirmation).toBeVisible();
  for (let i = 0; i < 6; i++) await page.keyboard.press("Tab");
  expect(await page.evaluate(() => !!document.activeElement?.closest("dialog"))).toBe(true);
  await page.keyboard.press("Escape");
  await expect(confirmation).not.toBeVisible();
  await expect(page.getByRole("button", { name: "Promote", exact: true })).toBeFocused();
  for (const route of ["staff", "children", "providers", "audit", "usage"]) {
    await page.goto(`/dashboard/admin/${route}`);
    await expect(page.locator("main h1")).toBeVisible();
    if (route === "staff") await expect(page.getByRole("button", { name: "Promote", exact: true })).toBeVisible();
    if (route === "children") await expect(page.getByText("Test Amina", { exact: true })).toBeVisible();
    if (route === "providers") await expect(page.getByLabel("Store a key", { exact: true }).first()).toBeVisible();
    if (route === "audit") await expect(page.getByText("No entries for this filter", { exact: true })).toBeVisible();
    if (route === "usage") await expect(page.getByText("No provider calls yet", { exact: true }).first()).toBeVisible();
    await fits(page);
    await page.screenshot({ path: `test-results/admin-${route}.png`, fullPage: true, caret: "initial" });
    await page.setViewportSize({ width: 390, height: 844 });
    await fits(page);
    await page.setViewportSize({ width: 1440, height: 1000 });
  }
  await page.goto("/dashboard/children/new");
  await expect(page).toHaveURL(/\/dashboard\/admin\/children$/);
});

test("admin sidebar fits laptop heights without a cramped navigation scroller", async ({ page }) => {
  await page.setViewportSize({ width: 1366, height: 650 });
  await login(page, "admin");
  const sidebar = page.locator("aside.sidebar");
  for (const height of [650, 768, 900]) {
    await page.setViewportSize({ width: 1366, height });
    expect(await sidebar.locator(".sidebar-inner").evaluate(node => node.scrollHeight <= node.clientHeight + 1)).toBe(true);
    expect(await sidebar.locator("nav").evaluate(node => node.scrollHeight <= node.clientHeight + 1)).toBe(true);
    await expect(sidebar.getByRole("link", { name: "Usage & cost" })).toBeInViewport();
    await expect(sidebar.getByRole("button", { name: /sign out/i })).toBeInViewport();
  }
  await page.setViewportSize({ width: 1366, height: 650 });
  await page.screenshot({ path: "test-results/admin-sidebar-laptop.png", caret: "initial" });
  await page.setViewportSize({ width: 1100, height: 450 });
  await sidebar.getByRole("button", { name: /sign out/i }).scrollIntoViewIfNeeded();
  await expect(sidebar.getByRole("button", { name: /sign out/i })).toBeInViewport();
  expect(await sidebar.locator("nav").evaluate(node => node.scrollHeight <= node.clientHeight + 1)).toBe(true);
  await page.setViewportSize({ width: 390, height: 700 });
  await page.getByRole("button", { name: "Open navigation" }).click();
  const drawer = page.getByRole("dialog", { name: "Workspace navigation" });
  await expect(drawer.getByRole("link", { name: "Usage & cost" })).toBeInViewport();
  await expect(drawer.getByRole("button", { name: /sign out/i })).toBeInViewport();
  await fits(page);
});

test("sign-in layout, required fields and guide remain usable on a small phone", async ({ page }) => {
  await page.setViewportSize({ width: 360, height: 800 });
  await page.goto("/login");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page.getByLabel("Email", { exact: true })).toBeFocused();
  await page.getByRole("heading", { name: "Welcome back" }).click();
  await page.screenshot({ path: "test-results/login-mobile.png", fullPage: true, caret: "initial" });
  await fits(page);
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.screenshot({ path: "test-results/login-desktop.png", fullPage: true, caret: "initial" });
  await login(page);
  await page.goto("/dashboard/guide");
  await expect(page.getByRole("heading", { name: "A clear next step" })).toBeVisible();
  await page.setViewportSize({ width: 360, height: 800 });
  await fits(page);
});

test("admin knowledge review saves feedback and text attachment without activating V3", async ({ page }) => {
  await login(page, "admin");
  await page.getByRole("link", { name: "Knowledge review", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Knowledge base review" })).toBeVisible();
  await page.getByLabel("Search entries").fill("V3-SL-M-024-1");
  await expect(page.getByText("1 matching entries", { exact: true })).toBeVisible();
  await expect(page.getByText("Roman-Urdu follow-up", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Save review feedback" })).toBeEnabled();
  await page.getByLabel("Reviewer name", { exact: true }).fill("Synthetic reviewer");
  await page.getByLabel("Set workflow status").selectOption("changes_requested");
  await page.getByLabel("Feedback and requested corrections").fill("Synthetic feedback: clarify the question wording.");
  await page.getByLabel("Attach written feedback", { exact: false }).setInputFiles({ name: "review.txt", mimeType: "text/plain", buffer: Buffer.from("Synthetic attached review document.") });
  await page.getByRole("button", { name: "Save review feedback" }).click();
  await expect(page.getByText("Feedback saved. Live knowledge base unchanged.")).toBeVisible();
  await page.reload();
  await expect(page.getByRole("heading", { name: "Knowledge base review" })).toBeVisible();
  await page.waitForTimeout(500);
  await page.getByLabel("Search entries").fill("V3-SL-M-024-1");
  await expect(page.getByLabel("Search entries")).toHaveValue("V3-SL-M-024-1");
  await expect(page.getByText("1 matching entries", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: /V3-SL-M-024-1/ }).click();
  await expect(page.getByText("Synthetic reviewer · Changes requested")).toBeVisible();
  await page.getByText("Attached: review.txt").click();
  await expect(page.getByText("Synthetic attached review document.")).toBeVisible();
  await page.setViewportSize({ width: 390, height: 844 });
  await fits(page);
  await page.screenshot({ path: "test-results/kb-review-mobile.png", fullPage: true, caret: "initial" });
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.screenshot({ path: "test-results/kb-review-desktop.png", fullPage: true, caret: "initial" });
  await page.getByLabel("Search entries").fill("no-such-reference");
  await expect(page.getByText("No matching entries. Adjust your filters.")).toBeVisible();
});
