import { NextResponse, type NextRequest } from "next/server";

import { SESSION_COOKIE } from "@/src/lib/auth/constants";
import { isSameOrigin } from "@/src/lib/auth/csrf";
import { backendFetch } from "@/src/lib/api/client";

interface Params {
  id: string;
}

export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<Params> },
) {
  if (!isSameOrigin(request)) {
    return NextResponse.json({ detail: "Forbidden" }, { status: 403 });
  }
  const token = request.cookies.get(SESSION_COOKIE)?.value;
  if (!token) return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
  const body = await request.text();
  const { id } = await params;
  try {
    const data = await backendFetch<unknown>(`/api/v1/admin/staff/${id}/active`, token, {
      method: "PATCH",
      body,
    });
    return NextResponse.json(data);
  } catch (error) {
    const status = error instanceof Error && "status" in error ? (error as { status: number }).status : 502;
    return NextResponse.json({ detail: "Request failed" }, { status });
  }
}
