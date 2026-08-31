import { cookies } from "next/headers";

import { SESSION_COOKIE } from "@/src/lib/auth/constants";

// Session token lives ONLY in an HttpOnly cookie (web-development.md
// MUST #3 / MUST-NOT #2) — never localStorage, never NEXT_PUBLIC_.
export { SESSION_COOKIE };

export function sessionCookieOptions() {
  return {
    httpOnly: true,
    sameSite: "lax" as const,
    // Secure flag on every non-local environment.
    secure: process.env.NODE_ENV === "production",
    path: "/",
    // Matches the backend access-token lifetime (JWT stub: 15 minutes).
    maxAge: 15 * 60,
  };
}

export async function getSessionToken(): Promise<string | null> {
  const store = await cookies();
  return store.get(SESSION_COOKIE)?.value ?? null;
}

// MUST #13: redirects are allow-listed — only internal /dashboard paths.
export function safeRedirectPath(candidate: string | null): string {
  if (candidate && candidate.startsWith("/dashboard")) {
    return candidate;
  }
  return "/dashboard";
}
