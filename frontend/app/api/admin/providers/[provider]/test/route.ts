import { NextResponse, type NextRequest } from "next/server";

import { SESSION_COOKIE } from "@/src/lib/auth/constants";
import { isSameOrigin } from "@/src/lib/auth/csrf";
import { ApiError } from "@/src/lib/api/client";
import { testProviderConnection } from "@/src/lib/api/admin";

interface Params {
  provider: string;
}

// One minimal real call against whichever credential source is ACTIVE
// (ADR-10 precedence). Reports success/failure only — never key material.
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

  const { provider } = await params;
  try {
    const result = await testProviderConnection(token, provider);
    return NextResponse.json({ result });
  } catch (error) {
    if (error instanceof ApiError && (error.status === 401 || error.status === 403)) {
      return NextResponse.json({ detail: "Admin role required" }, { status: error.status });
    }
    if (error instanceof ApiError && error.status === 404) {
      return NextResponse.json({ detail: "Unknown provider" }, { status: 404 });
    }
    if (error instanceof ApiError && error.status === 429) {
      return NextResponse.json(
        { detail: "Too many provider tests; try again later" },
        { status: 429 },
      );
    }
    return NextResponse.json({ detail: "Request failed" }, { status: 502 });
  }
}
