import { NextResponse, type NextRequest } from "next/server";
import { z } from "zod";

import { SESSION_COOKIE } from "@/src/lib/auth/constants";
import { isSameOrigin } from "@/src/lib/auth/csrf";
import { backendFetch } from "@/src/lib/api/client";
import { adminProxyError } from "@/src/lib/api/proxy-errors";

interface Params {
  id: string;
}

// The safe removal, and the one a refused DELETE points at. A reason is
// required: "why is this child no longer on the roster" is exactly what an
// auditor asks, and a blank answer is not an answer.
const bodySchema = z.object({ reason: z.string().trim().min(3).max(200) });

export async function POST(
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
    return NextResponse.json(
      { detail: "Give a short reason (at least 3 characters)." },
      { status: 422 },
    );
  }

  const { id } = await params;
  try {
    const data = await backendFetch<unknown>(
      `/api/v1/admin/children/${id}/archive`,
      token,
      { method: "POST", body: JSON.stringify(parsed.data) },
    );
    return NextResponse.json(data);
  } catch (error) {
    return adminProxyError(error, {
      409: "That child is already archived.",
      404: "That child no longer exists — reload the roster.",
    });
  }
}
