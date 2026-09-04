import type { NextRequest } from "next/server";

/**
 * MUST #4: CSRF protection on state-changing routes. SameSite=Lax cookies are
 * the baseline; this origin check closes the same-site POST gap.
 *
 * `nextUrl.origin` is derived from the Host the server actually received, so
 * behind any reverse proxy (a VS Code dev tunnel, ngrok, a staging load
 * balancer) it is the INTERNAL origin — `http://localhost:3000` — while the
 * browser truthfully sends the PUBLIC one. Comparing the two then rejects
 * every legitimate request with a 403.
 *
 * The fix is an explicit allowlist, never a relaxed comparison: forwarded
 * headers (`X-Forwarded-Host`) are attacker-controllable, so trusting them
 * would hand back exactly the CSRF gap this function exists to close.
 * `APP_ALLOWED_ORIGINS` is a comma-separated list of absolute origins; unset
 * means "same origin only", which is the original behaviour unchanged.
 */
function allowedOrigins(): string[] {
  const raw = process.env.APP_ALLOWED_ORIGINS;
  if (!raw) return [];
  return raw
    .split(",")
    .map((entry) => entry.trim().replace(/\/$/, ""))
    .filter((entry) => entry.length > 0);
}

export function isSameOrigin(request: NextRequest): boolean {
  const origin = request.headers.get("origin");
  // No Origin header at all: still refused. Browsers send it on every
  // cross-origin and same-origin POST, so its absence is not a browser.
  if (!origin) return false;
  if (origin === request.nextUrl.origin) return true;
  return allowedOrigins().includes(origin.replace(/\/$/, ""));
}
