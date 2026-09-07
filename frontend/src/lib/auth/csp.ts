// Content-Security-Policy for every HTML response, built per request around a
// fresh nonce. Lives here rather than inline in `proxy.ts` so it can be unit
// tested — the dev-only 'unsafe-eval' branch below is security-relevant and
// needs an assertion holding it to development, not a code review.
//
// Keep this file dependency-free: middleware runs on the edge runtime and must
// never transitively import `next/headers` (same rule as `constants.ts`).

/**
 * `next dev` compiles with eval-based source maps and its error overlay
 * evaluates code at runtime. A policy without 'unsafe-eval' therefore breaks
 * the dev server outright — "eval() is not supported" — and hides the very
 * overlay you need to read the error.
 *
 * Production builds do not eval, so the exemption is scoped to development.
 * `NODE_ENV` is inlined by Next at build time, so a production bundle cannot
 * carry this branch even by accident: there is no runtime switch to flip.
 */
export function devOnlyEval(nodeEnv: string | undefined): string {
  return nodeEnv === "production" ? "" : " 'unsafe-eval'";
}

export function contentSecurityPolicy(
  nonce: string,
  nodeEnv: string | undefined = process.env.NODE_ENV,
): string {
  return [
    "default-src 'self'",
    // 'strict-dynamic' + nonce means no inline script needs 'unsafe-inline';
    // Next attaches the nonce to its own hydration scripts.
    `script-src 'self' 'nonce-${nonce}' 'strict-dynamic'${devOnlyEval(nodeEnv)}`,
    // Styles keep 'unsafe-inline' on purpose: a nonce does not cover inline
    // style *attributes* (CSP3 governs those separately), and injected CSS is
    // a far smaller threat than injected script. Honest trade, not an oversight.
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data: blob:",
    "font-src 'self' data:",
    // The browser never calls the backend directly — everything goes through
    // this app's own /api proxies, so same-origin is the whole allowlist.
    "connect-src 'self'",
    // blob: is required for MediaRecorder playback in the voice capture flow.
    "media-src 'self' blob:",
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "frame-ancestors 'none'",
  ].join("; ");
}
