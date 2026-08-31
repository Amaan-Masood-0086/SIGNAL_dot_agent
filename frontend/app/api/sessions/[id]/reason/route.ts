import { NextResponse, type NextRequest } from "next/server";

import { SESSION_COOKIE } from "@/src/lib/auth/constants";
import { isSameOrigin } from "@/src/lib/auth/csrf";
import { ApiError } from "@/src/lib/api/client";
import { reasonSession } from "@/src/lib/api/reasoning";
import { reasoningInputSchema } from "@/src/lib/api/schemas";

interface Params {
  id: string;
}

// FEAT-06: one adaptive-loop turn — caretaker text in, outcome out
// (follow_up question or final graded result).
export async function POST(
  request: NextRequest,
  { params }: { params: Promise<Params> },
) {
  if (!isSameOrigin(request)) {
    return NextResponse.json({ detail: "Forbidden" }, { status: 403 });
  }
  const token = request.cookies.get(SESSION_COOKIE)?.value;
  if (!token) {
    return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
  }

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ detail: "Invalid request body" }, { status: 422 });
  }
  const parsed = reasoningInputSchema.safeParse(body);
  if (!parsed.success) {
    return NextResponse.json(
      { detail: parsed.error.issues.map((i) => i.message).join("; ") },
      { status: 422 },
    );
  }

  const { id } = await params;
  try {
    const result = await reasonSession(token, id, parsed.data);
    return NextResponse.json({ result });
  } catch (error) {
    if (error instanceof ApiError && (error.status === 401 || error.status === 403)) {
      return NextResponse.json({ detail: "Not permitted" }, { status: error.status });
    }
    if (error instanceof ApiError && error.status === 409) {
      return NextResponse.json(
        { detail: "This conversation has reached its turn limit or has ended" },
        { status: 409 },
      );
    }
    if (error instanceof ApiError && error.status === 429) {
      return NextResponse.json(
        { detail: "Too many requests; try again in a minute" },
        { status: 429 },
      );
    }
    if (error instanceof ApiError && error.status === 503) {
      return NextResponse.json(
        { detail: "Reasoning is unavailable right now; turns are still saved" },
        { status: 503 },
      );
    }
    return NextResponse.json({ detail: "Reasoning failed" }, { status: 502 });
  }
}
