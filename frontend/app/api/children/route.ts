import { NextResponse, type NextRequest } from "next/server";

import { isSameOrigin } from "@/src/lib/auth/csrf";
import { SESSION_COOKIE } from "@/src/lib/auth/constants";
import { ApiError } from "@/src/lib/api/client";
import { createChild, listChildren } from "@/src/lib/api/children";
import { childCreateSchema } from "@/src/lib/api/schemas";

// Institution-scoped roster for the dashboard. Scope is enforced by the
// backend from the signed JWT — the proxy only forwards.
export async function GET(request: NextRequest) {
  const token = request.cookies.get(SESSION_COOKIE)?.value;
  if (!token) {
    return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
  }
  // Allowlisted, not forwarded blind: an unrecognised value falls back to
  // "active" rather than reaching the backend. Without this the parameter was
  // silently dropped and ?status=archived quietly returned the active roster
  // — the worst kind of wrong, because it looks like it worked.
  const requested = request.nextUrl.searchParams.get("status");
  const status =
    requested === "archived" || requested === "all" ? requested : "active";

  try {
    const page = await listChildren(token, 1, 100, status);
    return NextResponse.json({ page });
  } catch (error) {
    if (error instanceof ApiError && (error.status === 401 || error.status === 403)) {
      return NextResponse.json({ detail: "Not permitted" }, { status: error.status });
    }
    return NextResponse.json({ detail: "Request failed" }, { status: 502 });
  }
}

// Browser → Next proxy → backend. The HttpOnly session cookie is read
// server-side; the JWT itself is never exposed to client JavaScript.
export async function POST(request: NextRequest) {
  if (!isSameOrigin(request)) {
    return NextResponse.json({ detail: "Forbidden" }, { status: 403 });
  }
  const token = request.cookies.get(SESSION_COOKIE)?.value;
  if (!token) {
    return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
  }

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ detail: "Invalid request body" }, { status: 422 });
  }
  const parsed = childCreateSchema.safeParse(body);
  if (!parsed.success) {
    return NextResponse.json(
      { detail: parsed.error.issues.map((i) => i.message).join("; ") },
      { status: 422 },
    );
  }

  try {
    const child = await createChild(token, parsed.data);
    return NextResponse.json({ child });
  } catch (error) {
    if (error instanceof ApiError && (error.status === 401 || error.status === 403)) {
      return NextResponse.json({ detail: "Not permitted" }, { status: error.status });
    }
    if (error instanceof ApiError && error.status === 422) {
      return NextResponse.json({ detail: "Rejected by server" }, { status: 422 });
    }
    // Never forward internal error details (MUST-NOT #16).
    return NextResponse.json({ detail: "Request failed" }, { status: 502 });
  }
}
