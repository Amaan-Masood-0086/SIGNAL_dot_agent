import { NextResponse, type NextRequest } from "next/server";

import { SESSION_COOKIE } from "@/src/lib/auth/constants";
import { backendFetch } from "@/src/lib/api/client";
import { adminProxyError } from "@/src/lib/api/proxy-errors";
import { ADMIN_PAGE_SIZE } from "@/src/lib/api/admin-schemas";

// Action filter is allowlisted by SHAPE (dotted lowercase identifier) so no
// arbitrary string reaches the backend query string.
const ACTION_PATTERN = /^[a-z_]+\.[a-z_]+$/;

export async function GET(request: NextRequest) {
  const token = request.cookies.get(SESSION_COOKIE)?.value;
  if (!token) return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });

  const rawPage = Number(request.nextUrl.searchParams.get("page") ?? "1");
  const page = Number.isInteger(rawPage) && rawPage >= 1 && rawPage <= 10_000 ? rawPage : 1;
  const action = request.nextUrl.searchParams.get("action");

  const qs = new URLSearchParams({ page: String(page), page_size: String(ADMIN_PAGE_SIZE) });
  if (action && ACTION_PATTERN.test(action)) qs.set("action", action);

  try {
    const data = await backendFetch<unknown>(`/api/v1/audit_log?${qs.toString()}`, token);
    return NextResponse.json(data);
  } catch (error) {
    return adminProxyError(error);
  }
}
