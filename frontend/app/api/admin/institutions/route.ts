import { NextResponse, type NextRequest } from "next/server";
import { z } from "zod";

import { SESSION_COOKIE } from "@/src/lib/auth/constants";
import { isSameOrigin } from "@/src/lib/auth/csrf";
import { backendFetch } from "@/src/lib/api/client";
import { adminProxyError } from "@/src/lib/api/proxy-errors";

// The picker behind every onboarding form: an explicit institution_id is
// unusable in a UI without a way to enumerate the choices.
export async function GET(request: NextRequest) {
  const token = request.cookies.get(SESSION_COOKIE)?.value;
  if (!token) return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
  try {
    return NextResponse.json(
      await backendFetch<unknown>("/api/v1/admin/institutions", token),
    );
  } catch (error) {
    return adminProxyError(error);
  }
}

// Allowlisted body — `is_synthetic` is deliberately NOT accepted: the backend
// forces it to match the environment, because a non-synthetic institution in
// a synthetic_only build is a dead end that silently refuses every child.
const bodySchema = z.object({
  name: z.string().trim().min(2).max(200),
});

export async function POST(request: NextRequest) {
  if (!isSameOrigin(request)) {
    return NextResponse.json({ detail: "Forbidden" }, { status: 403 });
  }
  const token = request.cookies.get(SESSION_COOKIE)?.value;
  if (!token) return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });

  const parsed = bodySchema.safeParse(await request.json().catch(() => null));
  if (!parsed.success) {
    return NextResponse.json(
      { detail: "Give the institution a name of at least 2 characters." },
      { status: 422 },
    );
  }

  try {
    const data = await backendFetch<unknown>("/api/v1/admin/institutions", token, {
      method: "POST",
      body: JSON.stringify(parsed.data),
    });
    return NextResponse.json(data, { status: 201 });
  } catch (error) {
    return adminProxyError(error);
  }
}
