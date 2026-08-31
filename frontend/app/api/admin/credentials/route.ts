import { NextResponse, type NextRequest } from "next/server";

import { SESSION_COOKIE } from "@/src/lib/auth/constants";
import { ApiError } from "@/src/lib/api/client";
import { listCredentials } from "@/src/lib/api/admin";

// ADR-10: credential status list. The backend schema is value-less by
// construction — this proxy passes through only {provider, is_active,
// masked_suffix, updated_at} rows.
export async function GET(request: NextRequest) {
  const token = request.cookies.get(SESSION_COOKIE)?.value;
  if (!token) {
    return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
  }
  try {
    const providers = await listCredentials(token);
    return NextResponse.json({ providers });
  } catch (error) {
    if (error instanceof ApiError && (error.status === 401 || error.status === 403)) {
      return NextResponse.json({ detail: "Admin role required" }, { status: error.status });
    }
    return NextResponse.json({ detail: "Request failed" }, { status: 502 });
  }
}
