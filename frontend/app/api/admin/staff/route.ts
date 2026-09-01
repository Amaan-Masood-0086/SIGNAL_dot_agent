import { NextResponse, type NextRequest } from "next/server";

import { SESSION_COOKIE } from "@/src/lib/auth/constants";
import { backendFetch } from "@/src/lib/api/client";
import { adminProxyError } from "@/src/lib/api/proxy-errors";
import { ADMIN_PAGE_SIZE } from "@/src/lib/api/admin-schemas";

function pageParam(request: NextRequest): number {
  const raw = Number(request.nextUrl.searchParams.get("page") ?? "1");
  return Number.isInteger(raw) && raw >= 1 && raw <= 10_000 ? raw : 1;
}

export async function GET(request: NextRequest) {
  const token = request.cookies.get(SESSION_COOKIE)?.value;
  if (!token) return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
  try {
    const data = await backendFetch<unknown>(
      `/api/v1/admin/staff?page=${pageParam(request)}&page_size=${ADMIN_PAGE_SIZE}`,
      token,
    );
    return NextResponse.json(data);
  } catch (error) {
    return adminProxyError(error);
  }
}
