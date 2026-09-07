import { describe, expect, it } from "vitest";

import { contentSecurityPolicy, devOnlyEval } from "@/src/lib/auth/csp";

/**
 * The dev-only 'unsafe-eval' exemption is the one part of this policy that
 * weakens it, so it gets the assertions. Everything else here is a tripwire:
 * these directives were each chosen for a reason recorded in `csp.ts`, and a
 * silent deletion should fail a test rather than a penetration test.
 */
describe("devOnlyEval", () => {
  it("is absent in production", () => {
    expect(devOnlyEval("production")).toBe("");
  });

  it("is present in development, where next dev needs it", () => {
    expect(devOnlyEval("development")).toContain("'unsafe-eval'");
  });

  it("fails safe only for production — an unset NODE_ENV is a dev shell", () => {
    // `next build` always sets production, so an undefined value means someone
    // ran this outside a Next build (a test runner, a script). Treating that as
    // development costs nothing; treating a genuine production build as dev is
    // the mistake worth preventing, and that path is pinned above.
    expect(devOnlyEval(undefined)).toContain("'unsafe-eval'");
    expect(devOnlyEval("test")).toContain("'unsafe-eval'");
  });
});

describe("contentSecurityPolicy", () => {
  it("carries the request nonce and strict-dynamic", () => {
    const csp = contentSecurityPolicy("abc123", "production");
    expect(csp).toContain("'nonce-abc123'");
    expect(csp).toContain("'strict-dynamic'");
  });

  it("never ships unsafe-eval to production", () => {
    expect(contentSecurityPolicy("abc123", "production")).not.toContain("unsafe-eval");
  });

  it("allows eval in development so the dev overlay can render", () => {
    expect(contentSecurityPolicy("abc123", "development")).toContain("'unsafe-eval'");
  });

  it("never allows unsafe-inline SCRIPT in any environment", () => {
    // style-src keeps 'unsafe-inline' deliberately (see csp.ts); script-src
    // must never gain it — that is what the nonce exists to avoid.
    for (const env of ["production", "development"]) {
      const scriptSrc = contentSecurityPolicy("abc123", env)
        .split("; ")
        .find((directive) => directive.startsWith("script-src"));
      expect(scriptSrc, env).not.toContain("unsafe-inline");
    }
  });

  it("keeps the directives the app actually depends on", () => {
    const csp = contentSecurityPolicy("abc123", "production");
    // blob: for MediaRecorder playback in the voice capture flow.
    expect(csp).toContain("media-src 'self' blob:");
    // The browser only ever talks to this app's own /api proxies.
    expect(csp).toContain("connect-src 'self'");
    expect(csp).toContain("frame-ancestors 'none'");
    expect(csp).toContain("object-src 'none'");
  });
});
