import type { NextRequest } from "next/server";

// MUST #4: CSRF protection on state-changing routes. SameSite=Lax cookies are
// the baseline; this origin check closes the same-site POST gap.
export function isSameOrigin(request: NextRequest): boolean {
  const origin = request.headers.get("origin");
  if (!origin) return false;
  return origin === request.nextUrl.origin;
}
