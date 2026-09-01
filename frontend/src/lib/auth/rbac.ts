// Server-side RBAC helpers. Deny by default: every dashboard surface calls
// `requireStaff()`, every admin surface calls `requireAdmin()`.
//
// This is a UX gate, not the security boundary — the backend re-checks the
// DB staff row on every admin endpoint (`get_current_admin_staff`). Gating
// here stops caretakers being shown navigation that would only 403.

import { cache } from "react";
import { redirect } from "next/navigation";

import { getMe, type Me } from "@/src/lib/api/me";
import { getSessionToken } from "@/src/lib/auth/session";

export type { Me };

// `cache()` dedupes the identity call across the layout + page of a single
// render (backendFetch is `no-store`, so without this each caller refetches).
export const getCurrentStaff = cache(async (): Promise<Me | null> => {
  const token = await getSessionToken();
  if (!token) return null;
  try {
    return await getMe(token);
  } catch {
    return null;
  }
});

/** Session required. An unknown/expired session goes back to sign-in. */
export async function requireStaff(): Promise<Me> {
  const me = await getCurrentStaff();
  if (!me) {
    redirect("/login");
  }
  return me;
}

/** True only when the DB staff row itself grants admin (see `/auth/me`). */
export function isAdmin(me: Me | null): boolean {
  return me?.is_admin === true;
}
