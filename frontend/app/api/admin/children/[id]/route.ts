import { NextResponse, type NextRequest } from "next/server";
import { z } from "zod";

import { SESSION_COOKIE } from "@/src/lib/auth/constants";
import { isSameOrigin } from "@/src/lib/auth/csrf";
import { backendFetch } from "@/src/lib/api/client";
import { adminProxyError } from "@/src/lib/api/proxy-errors";

interface Params {
  id: string;
}

/**
 * DELETE removes a child permanently — and the backend allows it ONLY when
 * the record has no screening history. The 409 it returns is the useful case,
 * not an error to flatten: it names what exists and points at archive, which
 * takes the child off the roster without destroying the clinical record.
 */
export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<Params> },
) {
  if (!isSameOrigin(request)) {
    return NextResponse.json({ detail: "Forbidden" }, { status: 403 });
  }
  const token = request.cookies.get(SESSION_COOKIE)?.value;
  if (!token) return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });

  const { id } = await params;
  try {
    const data = await backendFetch<unknown>(`/api/v1/admin/children/${id}`, token, {
      method: "DELETE",
    });
    return NextResponse.json(data);
  } catch (error) {
    return adminProxyError(error, {
      // The backend's 409 carries the counts and the recommendation; a
      // generic sentence here would throw away the only useful part.
      409:
        "This child has a screening record. Deleting it would destroy " +
        "clinical evidence — archive them instead.",
      404: "That child no longer exists — reload the roster.",
    });
  }
}

// Assignment: who is responsible for this child. `null` clears it.
const assignSchema = z.object({
  staff_id: z.string().uuid().nullable(),
});

export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<Params> },
) {
  if (!isSameOrigin(request)) {
    return NextResponse.json({ detail: "Forbidden" }, { status: 403 });
  }
  const token = request.cookies.get(SESSION_COOKIE)?.value;
  if (!token) return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });

  const parsed = assignSchema.safeParse(await request.json().catch(() => null));
  if (!parsed.success) {
    return NextResponse.json({ detail: "Choose a staff member." }, { status: 422 });
  }

  const { id } = await params;
  try {
    const data = await backendFetch<unknown>(
      `/api/v1/admin/children/${id}/assignment`,
      token,
      { method: "PATCH", body: JSON.stringify(parsed.data) },
    );
    return NextResponse.json(data);
  } catch (error) {
    return adminProxyError(error, {
      409:
        "That staff member cannot take this child — they either work at a " +
        "different institution or their account is deactivated.",
      404: "That child or staff member no longer exists — reload.",
    });
  }
}
