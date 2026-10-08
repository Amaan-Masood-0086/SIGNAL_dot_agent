import { defineConfig } from "@playwright/test";

// Real Next pages + BFF against an isolated, in-memory synthetic fixture API.
// No database, authentication service, provider keys or paid calls are used.
export default defineConfig({
  testDir: "./e2e",
  workers: 1,
  timeout: 90000,
  expect: { timeout: 15000 },
  use: { baseURL: "http://127.0.0.1:3015", browserName: "chromium", channel: "chrome", screenshot: "only-on-failure", trace: "retain-on-failure" },
  webServer: [
    { command: "node e2e/fixture-server.mjs", url: "http://127.0.0.1:18119/health", reuseExistingServer: false },
    { command: "npm run dev -- --hostname 127.0.0.1 --port 3015", url: "http://127.0.0.1:3015/login", timeout: 180000, reuseExistingServer: false, env: { SIGNAL_UI_TEST: "1", BACKEND_URL: "http://127.0.0.1:18119", APP_ALLOWED_ORIGINS: "http://127.0.0.1:3015" } },
  ],
});
