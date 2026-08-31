import { NextResponse, type NextRequest } from "next/server";

import { SESSION_COOKIE } from "@/src/lib/auth/constants";
import { ApiError } from "@/src/lib/api/client";
import { listProviderStatuses } from "@/src/lib/api/admin";

// Provider status cards — configured/not-configured + SOURCE (ui/env).
// Values can never appear: the backend schema has no field for them.
export async function GET(request: NextRequest) {
  const token = request.cookies.get(SESSION_COOKIE)?.value;
  if (!token) {
    return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
  }
  try {
    const providers = await listProviderStatuses(token);
    return NextResponse.json({ providers });
  } catch (error) {
    if (error instanceof ApiError && (error.status === 401 || error.status === 403)) {
      return NextResponse.json({ detail: "Admin role required" }, { status: error.status });
    }
    return NextResponse.json({ detail: "Request failed" }, { status: 502 });
  }
}
