import { NextResponse, type NextRequest } from "next/server";
import { z } from "zod";

import { SESSION_COOKIE } from "@/src/lib/auth/constants";
import { isSameOrigin } from "@/src/lib/auth/csrf";
import { backendFetch } from "@/src/lib/api/client";
import { adminProxyError } from "@/src/lib/api/proxy-errors";

interface Params {
  id: string;
}

// Allowlisted body (MUST #16 / API3): only `role`, and only a known role —
// the raw request body is never forwarded verbatim.
const bodySchema = z.object({ role: z.enum(["caretaker", "admin"]) });

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
    return NextResponse.json({ detail: "Unknown role" }, { status: 422 });
  }

  const { id } = await params;
  try {
    const data = await backendFetch<unknown>(`/api/v1/admin/staff/${id}/role`, token, {
      method: "PATCH",
      body: JSON.stringify(parsed.data),
    });
    return NextResponse.json(data);
  } catch (error) {
    return adminProxyError(error);
  }
}
