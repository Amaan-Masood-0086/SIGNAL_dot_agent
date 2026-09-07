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
      `/api/v1/admin/children?page=${pageParam(request)}&page_size=${ADMIN_PAGE_SIZE}`,
      token,
    );
    return NextResponse.json(data);
  } catch (error) {
    return adminProxyError(error);
  }
}

// Mirrors the backend's AdminChildCreate, including the ADR-02 rule that
// confirmed-DOB and estimated-range are mutually exclusive. `institution_id`
// is REQUIRED here and absent from the caretaker form on purpose: a
// system-level admin has no care institution of their own, so they name it.
const createSchema = z
  .object({
    name: z.string().trim().min(1).max(200),
    institution_id: z.string().uuid(),
    dob_confirmed: z.boolean(),
    dob: z.string().nullable().optional(),
    estimated_age_range: z.string().max(50).nullable().optional(),
    estimated_age_note: z.string().nullable().optional(),
  })
  .superRefine((value, ctx) => {
    if (value.dob_confirmed) {
      if (!value.dob) {
        ctx.addIssue({
          code: "custom",
          path: ["dob"],
          message: "Date of birth is required when it is confirmed",
        });
      }
      if (value.estimated_age_range || value.estimated_age_note) {
        ctx.addIssue({
          code: "custom",
          path: ["estimated_age_range"],
          message: "Leave estimated-age fields empty for a confirmed DOB",
        });
      }
    } else {
      if (!value.estimated_age_range) {
        ctx.addIssue({
          code: "custom",
          path: ["estimated_age_range"],
          message: "Estimated age range is required when DOB is not confirmed",
        });
      }
      if (value.dob) {
        ctx.addIssue({
          code: "custom",
          path: ["dob"],
          message: "Do not enter a DOB when the age is estimated",
        });
      }
    }
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
      { detail: parsed.error.issues.map((i) => i.message).join("; ") },
      { status: 422 },
    );
  }

  try {
    const data = await backendFetch<unknown>("/api/v1/admin/children", token, {
      method: "POST",
      body: JSON.stringify(parsed.data),
    });
    return NextResponse.json(data, { status: 201 });
  } catch (error) {
    return adminProxyError(error, {
      404: "That institution no longer exists — reload and try again.",
      422: "The age details do not match the confirmed/estimated rule.",
    });
  }
}
