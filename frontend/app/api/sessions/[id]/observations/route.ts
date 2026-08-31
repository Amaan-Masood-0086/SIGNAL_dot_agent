import { NextResponse, type NextRequest } from "next/server";

import { SESSION_COOKIE } from "@/src/lib/auth/constants";
import { isSameOrigin } from "@/src/lib/auth/csrf";
import { ApiError } from "@/src/lib/api/client";
import { addObservation, listObservations } from "@/src/lib/api/sessions";
import { observationCreateSchema } from "@/src/lib/api/schemas";

interface Params {
  id: string;
}

// Capture one caretaker turn. Voice transcripts and typed text both POST the
// same body shape here — the stored observation is identical either way.
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
  const parsed = observationCreateSchema.safeParse(body);
  if (!parsed.success) {
    return NextResponse.json(
      { detail: parsed.error.issues.map((i) => i.message).join("; ") },
      { status: 422 },
    );
  }

  const { id } = await params;
  try {
    const observation = await addObservation(token, id, parsed.data);
    return NextResponse.json({ observation }, { status: 201 });
  } catch (error) {
    if (error instanceof ApiError && (error.status === 401 || error.status === 403)) {
      return NextResponse.json({ detail: "Not permitted" }, { status: error.status });
    }
    if (error instanceof ApiError && error.status === 409) {
      return NextResponse.json({ detail: "Session already finished" }, { status: 409 });
    }
    if (error instanceof ApiError && error.status === 429) {
      return NextResponse.json(
        { detail: "Too many requests; try again in a minute" },
        { status: 429 },
      );
    }
    if (error instanceof ApiError && error.status === 422) {
      return NextResponse.json({ detail: "Rejected by server" }, { status: 422 });
    }
    return NextResponse.json({ detail: "Request failed" }, { status: 502 });
  }
}

// Turn history (paginated) for rendering the conversation.
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<Params> },
) {
  const token = request.cookies.get(SESSION_COOKIE)?.value;
  if (!token) {
    return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
  }

  const { id } = await params;
  const page = Number(request.nextUrl.searchParams.get("page") ?? 1);
  const pageSize = Number(request.nextUrl.searchParams.get("page_size") ?? 50);
  if (!Number.isInteger(page) || page < 1 || !Number.isInteger(pageSize) || pageSize < 1) {
    return NextResponse.json({ detail: "Invalid pagination" }, { status: 422 });
  }

  try {
    const result = await listObservations(token, id, page, pageSize);
    return NextResponse.json({ result });
  } catch (error) {
    if (error instanceof ApiError && (error.status === 401 || error.status === 403)) {
      return NextResponse.json({ detail: "Not permitted" }, { status: error.status });
    }
    return NextResponse.json({ detail: "Request failed" }, { status: 502 });
  }
}
