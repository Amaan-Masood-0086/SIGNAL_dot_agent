import { NextResponse, type NextRequest } from "next/server";

import { SESSION_COOKIE } from "@/src/lib/auth/constants";
import { ApiError } from "@/src/lib/api/client";
import { getFlag } from "@/src/lib/api/flags";

interface Params {
  id: string;
}

// Read-only: the reasoning panel calls this after a conclusion to render the
// resolved knowledge-base basis (citation + description + source) instead of
// opaque refs. No write verb exists here — flags are created by the
// reasoning pipeline, never by the browser.
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<Params> },
) {
  const token = request.cookies.get(SESSION_COOKIE)?.value;
  if (!token) {
    return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
  }

  const { id } = await params;
  try {
    const flag = await getFlag(token, id);
    return NextResponse.json({ flag });
  } catch (error) {
    // Backend returns 403 for both "not found" and "other institution" —
    // surface that uniformly without leaking which case it was (IDOR T2).
    if (error instanceof ApiError && (error.status === 401 || error.status === 403)) {
      return NextResponse.json({ detail: "Not permitted" }, { status: error.status });
    }
    return NextResponse.json({ detail: "Request failed" }, { status: 502 });
  }
}
