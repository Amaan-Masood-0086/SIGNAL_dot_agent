import { NextResponse, type NextRequest } from "next/server";

import { ApiError } from "@/src/lib/api/client";
import { createSession } from "@/src/lib/api/sessions";
import { sessionCreateSchema } from "@/src/lib/api/schemas";
import { isSameOrigin } from "@/src/lib/auth/csrf";
import { SESSION_COOKIE } from "@/src/lib/auth/constants";

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
  const parsed = sessionCreateSchema.safeParse(body);
  if (!parsed.success) {
    return NextResponse.json(
      { detail: parsed.error.issues.map((i) => i.message).join("; ") },
      { status: 422 },
    );
  }

  try {
    const session = await createSession(token, parsed.data);
    return NextResponse.json({ session }, { status: 201 });
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
