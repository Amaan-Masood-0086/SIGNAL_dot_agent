import { NextResponse, type NextRequest } from "next/server";
import { z } from "zod";

import { SESSION_COOKIE } from "@/src/lib/auth/constants";
import { isSameOrigin } from "@/src/lib/auth/csrf";
import { backendFetch } from "@/src/lib/api/client";
import { adminProxyError } from "@/src/lib/api/proxy-errors";

interface Params {
  id: string;
}

const bodySchema = z.object({ is_active: z.boolean() });

export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<Params> },
) {
  if (!isSameOrigin(request)) {
    return NextResponse.json({ detail: "Forbidden" }, { status: 403 });
  }
  const token = request.cookies.get(SESSION_COOKIE)?.value;
  if (!token) return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });

  const parsed = bodySchema.safeParse(await request.json().catch(() => null));
  if (!parsed.success) {
    return NextResponse.json({ detail: "Invalid request body" }, { status: 422 });
  }

  const { id } = await params;
  try {
    const data = await backendFetch<unknown>(`/api/v1/admin/staff/${id}/active`, token, {
      method: "PATCH",
      body: JSON.stringify(parsed.data),
    });
    return NextResponse.json(data);
  } catch (error) {
    return adminProxyError(error);
  }
}
