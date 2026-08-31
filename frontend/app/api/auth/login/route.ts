import { NextResponse, type NextRequest } from "next/server";
import { z } from "zod";

import { isSameOrigin } from "@/src/lib/auth/csrf";
import { SESSION_COOKIE, sessionCookieOptions } from "@/src/lib/auth/session";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

const credentialsSchema = z.object({
  email: z.string().email().max(320),
  password: z.string().min(1).max(256),
});

// Server-side proxy to the backend auth stub. The JWT never touches client
// storage — it is exchanged here and sealed into an HttpOnly cookie.
export async function POST(request: NextRequest) {
  if (!isSameOrigin(request)) {
    return NextResponse.json({ detail: "Forbidden" }, { status: 403 });
  }

  let parsed: z.infer<typeof credentialsSchema>;
  try {
    parsed = credentialsSchema.parse(await request.json());
  } catch {
    return NextResponse.json({ detail: "Invalid credentials" }, { status: 422 });
  }

  let backendResponse: Response;
  try {
    backendResponse = await fetch(`${BACKEND_URL}/api/v1/auth/token`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(parsed),
      cache: "no-store",
    });
  } catch {
    return NextResponse.json(
      { detail: "Authentication service unavailable" },
      { status: 502 },
    );
  }

  if (!backendResponse.ok) {
    // Do not echo backend error internals (MUST-NOT #16).
    return NextResponse.json({ detail: "Authentication failed" }, { status: 401 });
  }

  const envelope = (await backendResponse.json()) as {
    data?: { access_token?: string };
  };
  const token = envelope.data?.access_token;
  if (!token) {
    return NextResponse.json({ detail: "Authentication failed" }, { status: 401 });
  }

  const response = NextResponse.json({ success: true });
  response.cookies.set(SESSION_COOKIE, token, sessionCookieOptions());
  return response;
}
