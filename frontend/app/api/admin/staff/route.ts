import { NextResponse, type NextRequest } from "next/server";

import { SESSION_COOKIE } from "@/src/lib/auth/constants";
import { backendFetch } from "@/src/lib/api/client";

export async function GET(request: NextRequest) {
  const token = request.cookies.get(SESSION_COOKIE)?.value;
  if (!token) return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
  const page = request.nextUrl.searchParams.get("page") ?? "1";
  try {
    const data = await backendFetch<unknown>(
      `/api/v1/admin/staff?page=${page}&page_size=50`,
      token,
    );
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ detail: "Admin role required" }, { status: 403 });
  }
}
