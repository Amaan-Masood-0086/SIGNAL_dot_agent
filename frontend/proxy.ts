import { NextResponse, type NextRequest } from "next/server";

import { SESSION_COOKIE } from "@/src/lib/auth/constants";

/**
 * Route protection + Content-Security-Policy. Next 16's `proxy` convention
 * (formerly `middleware`).
 *
 * Signature verification of the JWT happens on the backend on every API call
 * — this layer enforces session presence, the no-cache rule for
 * authenticated HTML, and the per-request CSP nonce.
 *
 * The matcher covers every page so CSP ships everywhere, but the auth
 * redirect is scoped to /dashboard inside the handler: widening the matcher
 * without that guard would redirect /login to /login forever.
 */
function contentSecurityPolicy(nonce: string): string {
  return [
    "default-src 'self'",
    // 'strict-dynamic' + nonce means no inline script needs 'unsafe-inline';
    // Next attaches the nonce to its own hydration scripts.
    `script-src 'self' 'nonce-${nonce}' 'strict-dynamic'`,
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

export function proxy(request: NextRequest) {
  const nonce = crypto.randomUUID().replace(/-/g, "");
  const csp = contentSecurityPolicy(nonce);

  const isDashboard = request.nextUrl.pathname.startsWith("/dashboard");

  if (isDashboard && !request.cookies.get(SESSION_COOKIE)?.value) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("next", request.nextUrl.pathname);
    const redirect = NextResponse.redirect(loginUrl);
    redirect.headers.set("Content-Security-Policy", csp);
    return redirect;
  }

  // The nonce must reach the renderer on the REQUEST headers — that is how
  // Next knows to stamp it onto its own script tags.
  const requestHeaders = new Headers(request.headers);
  requestHeaders.set("x-nonce", nonce);
  requestHeaders.set("Content-Security-Policy", csp);

  const response = NextResponse.next({ request: { headers: requestHeaders } });
  response.headers.set("Content-Security-Policy", csp);

  // MUST #18 / MUST-NOT #8: authenticated HTML is never cached at CDN/edge.
  if (isDashboard) {
    response.headers.set("Cache-Control", "private, no-store");
  }
  return response;
}

export const config = {
  // Every page, minus immutable static assets — adding a per-request header
  // to those only defeats their caching and they carry no injection surface.
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
