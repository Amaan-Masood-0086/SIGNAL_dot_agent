import { NextResponse, type NextRequest } from "next/server";

import { SESSION_COOKIE } from "@/src/lib/auth/constants";
import { isSameOrigin } from "@/src/lib/auth/csrf";
import { backendFetch } from "@/src/lib/api/client";
import { adminProxyError } from "@/src/lib/api/proxy-errors";

interface Params {
  id: string;
}

// Archiving is reversible on purpose — a wrong archive must not need a DBA.
export async function POST(
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
    const data = await backendFetch<unknown>(
      `/api/v1/admin/children/${id}/restore`,
      token,
      { method: "POST", body: "" },
    );
    return NextResponse.json(data);
  } catch (error) {
    return adminProxyError(error, {
      409: "That child is not archived.",
      404: "That child no longer exists — reload the roster.",
    });
  }
}
