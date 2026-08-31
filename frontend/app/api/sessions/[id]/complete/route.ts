import { NextResponse, type NextRequest } from "next/server";

import { SESSION_COOKIE } from "@/src/lib/auth/constants";
import { isSameOrigin } from "@/src/lib/auth/csrf";
import { ApiError } from "@/src/lib/api/client";
import { completeSession } from "@/src/lib/api/sessions";

interface Params {
  id: string;
}

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
    const session = await completeSession(token, id);
    return NextResponse.json({ session });
  } catch (error) {
    if (error instanceof ApiError && (error.status === 401 || error.status === 403)) {
      return NextResponse.json({ detail: "Not permitted" }, { status: error.status });
    }
    if (error instanceof ApiError && error.status === 409) {
      return NextResponse.json({ detail: "Session already finished" }, { status: 409 });
    }
    return NextResponse.json({ detail: "Request failed" }, { status: 502 });
  }
}
