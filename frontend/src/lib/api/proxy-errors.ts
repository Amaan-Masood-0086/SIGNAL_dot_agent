import { NextResponse } from "next/server";

import { ApiError } from "@/src/lib/api/client";

// Curated, non-internal messages for the admin write proxies. The backend's
// own strings are never echoed (MUST-NOT #16) — these are our own copy, keyed
// by status, so a business rule like "you cannot demote yourself" can still
// reach the user instead of collapsing into "Request failed".
const MESSAGES: Record<number, string> = {
  401: "Your session expired. Sign in again.",
  403: "Admin role required.",
  404: "That record no longer exists.",
  409: "Blocked: an admin cannot change their own role or active state. Ask another admin.",
  422: "The request was rejected as invalid.",
  429: "Too many attempts. Try again in a few minutes.",
};

export function adminProxyError(error: unknown): NextResponse {
  const status = error instanceof ApiError ? error.status : 502;
  return NextResponse.json(
    { detail: MESSAGES[status] ?? "The request could not be completed." },
    { status: MESSAGES[status] ? status : 502 },
  );
}
