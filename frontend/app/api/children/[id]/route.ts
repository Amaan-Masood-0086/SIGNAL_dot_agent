import { NextResponse, type NextRequest } from "next/server";

import { SESSION_COOKIE } from "@/src/lib/auth/constants";
import { ApiError } from "@/src/lib/api/client";
import { getChild } from "@/src/lib/api/children";

interface Params {
  id: string;
}

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
    const child = await getChild(token, id);
    return NextResponse.json({ child });
  } catch (error) {
    // Backend returns 403 for both "not found" and "other institution" —
    // surface that uniformly without leaking which case it was (IDOR T2).
    if (error instanceof ApiError && (error.status === 401 || error.status === 403)) {
      return NextResponse.json({ detail: "Not permitted" }, { status: error.status });
    }
    return NextResponse.json({ detail: "Request failed" }, { status: 502 });
  }
}
