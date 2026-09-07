import { NextResponse, type NextRequest } from "next/server";
import { z } from "zod";

import { SESSION_COOKIE } from "@/src/lib/auth/constants";
import { isSameOrigin } from "@/src/lib/auth/csrf";
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

// Allowlisted body. No password field: login does not verify passwords yet
// (FEAT-12), so collecting one would imply a guarantee the system does not
// make — the backend stores an unusable placeholder instead.
const createSchema = z.object({
  email: z.string().trim().email().max(320),
  role: z.enum(["caretaker", "admin"]),
  institution_id: z.string().uuid(),
});

export async function POST(request: NextRequest) {
  if (!isSameOrigin(request)) {
    return NextResponse.json({ detail: "Forbidden" }, { status: 403 });
  }
  const token = request.cookies.get(SESSION_COOKIE)?.value;
  if (!token) return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });

  const parsed = createSchema.safeParse(await request.json().catch(() => null));
  if (!parsed.success) {
    return NextResponse.json(
      { detail: "Enter a valid email address and choose a role and institution." },
      { status: 422 },
    );
  }

  try {
    const data = await backendFetch<unknown>("/api/v1/admin/staff", token, {
      method: "POST",
      body: JSON.stringify(parsed.data),
    });
    return NextResponse.json(data, { status: 201 });
  } catch (error) {
    // A status code is not a meaning: the shared 409 copy is about an admin
    // changing their OWN role, which has nothing to do with a taken email.
    return adminProxyError(error, {
      409: "A staff account with that email already exists.",
      404: "That institution no longer exists — reload and try again.",
    });
  }
}
