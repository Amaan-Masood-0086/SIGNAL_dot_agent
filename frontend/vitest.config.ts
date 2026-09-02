import { defineConfig } from "vitest/config";
import path from "node:path";

// Unit tests for pure logic only — the RBAC nav filter and the clinical
// grade labelling. Both are plain modules with no DOM, so no jsdom
// environment is needed and the suite stays fast enough to run on every PR.
export default defineConfig({
  test: {
    environment: "node",
    include: ["src/**/*.test.ts"],
  },
  resolve: {
    alias: { "@": path.resolve(__dirname) },
  },
});
