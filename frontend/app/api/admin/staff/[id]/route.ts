import { NextResponse, type NextRequest } from "next/server";

import { SESSION_COOKIE } from "@/src/lib/auth/constants";
import { isSameOrigin } from "@/src/lib/auth/csrf";
import { backendFetch } from "@/src/lib/api/client";
import { adminProxyError } from "@/src/lib/api/proxy-errors";

interface Params {
  id: string;
}

/**
 * DELETE removes a staff account permanently — and only when it never did
 * anything. Once the account has run sessions or spent provider budget the
 * backend refuses, because the audit chain names it as the actor behind
 * graded findings and a row that no longer exists cannot answer "who did
 * this". Deactivation removes the access and keeps the attribution.
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
    const data = await backendFetch<unknown>(`/api/v1/admin/staff/${id}`, token, {
      method: "DELETE",
    });
    return NextResponse.json(data);
  } catch (error) {
    return adminProxyError(error, {
      409:
        "This account has activity on the record, or is your own. " +
        "Deactivate it instead — that removes access and keeps the audit trail.",
      404: "That account no longer exists — reload the directory.",
    });
  }
}
