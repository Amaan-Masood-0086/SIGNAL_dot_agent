import { NextResponse, type NextRequest } from "next/server";
import { z } from "zod";

import { SESSION_COOKIE } from "@/src/lib/auth/constants";
import { ApiError, backendFetch } from "@/src/lib/api/client";
import { isSameOrigin } from "@/src/lib/auth/csrf";

interface Params {
  id: string;
}

// Allowlisted body — the reason is the only thing the browser may set, and
// the backend re-validates the same minimum length. Archiving is reversible,
// but it still changes what a roster shows, so it is a state-changing route
// and carries the CSRF origin check.
const bodySchema = z.object({
  reason: z.string().trim().min(3).max(200),
});

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<Params> },
) {
  if (!isSameOrigin(request)) {
    return NextResponse.json({ detail: "Forbidden" }, { status: 403 });
  }

  const token = request.cookies.get(SESSION_COOKIE)?.value;
  if (!token) {
    return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
  }

  let parsed: z.infer<typeof bodySchema>;
  try {
    parsed = bodySchema.parse(await request.json());
  } catch {
    return NextResponse.json(
      { detail: "Give a short reason (at least 3 characters)" },
      { status: 422 },
    );
  }

  const { id } = await params;
  try {
    await backendFetch(`/api/v1/children/${id}/archive`, token, {
      method: "POST",
      body: JSON.stringify(parsed),
    });
    return NextResponse.json({ success: true });
  } catch (error) {
    if (error instanceof ApiError) {
      if (error.status === 409) {
        return NextResponse.json(
          { detail: "This child is already archived." },
          { status: 409 },
        );
      }
      // 403 covers both "not found" and "another institution" (IDOR T2).
      if (error.status === 401 || error.status === 403) {
        return NextResponse.json({ detail: "Not permitted" }, { status: error.status });
      }
    }
    return NextResponse.json({ detail: "Request failed" }, { status: 502 });
  }
}
