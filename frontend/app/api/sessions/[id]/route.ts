import { NextResponse, type NextRequest } from "next/server";

import { SESSION_COOKIE } from "@/src/lib/auth/constants";
import { ApiError } from "@/src/lib/api/client";
import { getSession } from "@/src/lib/api/sessions";

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
    const session = await getSession(token, id);
    return NextResponse.json({ session });
  } catch (error) {
    // Uniform 403 for not-found vs other-institution (IDOR T2) — do not leak
    // which case it was.
    if (error instanceof ApiError && (error.status === 401 || error.status === 403)) {
      return NextResponse.json({ detail: "Not permitted" }, { status: error.status });
    }
    return NextResponse.json({ detail: "Request failed" }, { status: 502 });
  }
}
