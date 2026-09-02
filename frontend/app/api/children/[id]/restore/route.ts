import { NextResponse, type NextRequest } from "next/server";

import { SESSION_COOKIE } from "@/src/lib/auth/constants";
import { ApiError, backendFetch } from "@/src/lib/api/client";
import { isSameOrigin } from "@/src/lib/auth/csrf";

interface Params {
  id: string;
}

// Undo for an archive. No body: there is nothing for the caller to choose.
// Still state-changing, so still behind the CSRF origin check.
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

  const { id } = await params;
  try {
    await backendFetch(`/api/v1/children/${id}/restore`, token, {
      method: "POST",
    });
    return NextResponse.json({ success: true });
  } catch (error) {
    if (error instanceof ApiError) {
      if (error.status === 409) {
        return NextResponse.json(
          { detail: "This child is not archived." },
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
