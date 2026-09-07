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

/**
 * `overrides` exists because a status code is not a meaning. 409 on a role
 * change means "you cannot demote yourself"; 409 on staff creation means
 * "that email is taken"; 404 when creating means "that institution does not
 * exist", not "the record is gone". Sending one canned sentence for all of
 * them is how three different failures once all read "check your
 * credentials" — the exact bug this file was written to stop.
 */
export function adminProxyError(
  error: unknown,
  overrides: Record<number, string> = {},
): NextResponse {
  const status = error instanceof ApiError ? error.status : 502;
  const message = overrides[status] ?? MESSAGES[status];
  return NextResponse.json(
    { detail: message ?? "The request could not be completed." },
    { status: message ? status : 502 },
  );
}
