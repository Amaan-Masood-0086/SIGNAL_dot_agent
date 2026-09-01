import { NextResponse, type NextRequest } from "next/server";
import { z } from "zod";

import { SESSION_COOKIE } from "@/src/lib/auth/constants";
import { isSameOrigin } from "@/src/lib/auth/csrf";
import { ApiError } from "@/src/lib/api/client";
import { deleteCredential, saveCredential } from "@/src/lib/api/admin";

interface Params {
  provider: string;
}

const bodySchema = z.object({
  value: z.string().trim().min(1).max(2000),
  // Optional model override (migration 0005). Bounded + trimmed here so an
  // oversized or blank string never reaches the backend; empty means
  // "no override" and is normalised to null.
  model: z.string().trim().max(120).nullish(),
});

// ADR-10 write-only contract: the value goes IN, and the response carries
// only masked_suffix + updated_at — never an echo of what was typed.
export async function PUT(
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
  const parsed = bodySchema.safeParse(body);
  if (!parsed.success) {
    return NextResponse.json(
      { detail: parsed.error.issues.map((i) => i.message).join("; ") },
      { status: 422 },
    );
  }

  const { provider } = await params;
  try {
    const result = await saveCredential(
      token,
      provider,
      parsed.data.value,
      parsed.data.model?.trim() ? parsed.data.model.trim() : null,
    );
    return NextResponse.json({ result });
  } catch (error) {
    if (error instanceof ApiError && (error.status === 401 || error.status === 403)) {
      return NextResponse.json({ detail: "Admin role required" }, { status: error.status });
    }
    if (error instanceof ApiError && error.status === 404) {
      return NextResponse.json({ detail: "Unknown provider" }, { status: 404 });
    }
    if (error instanceof ApiError && error.status === 429) {
      return NextResponse.json(
        { detail: "Too many credential writes; try again later" },
        { status: 429 },
      );
    }
    if (error instanceof ApiError && error.status === 503) {
      return NextResponse.json(
        { detail: "Credential storage is unavailable (encryption key missing)" },
        { status: 503 },
      );
    }
    return NextResponse.json({ detail: "Request failed" }, { status: 502 });
  }
}

// Soft delete: deactivates the stored credential; the system falls back to
// the environment variable per the ADR-10 precedence rule.
export async function DELETE(
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

  const { provider } = await params;
  try {
    const result = await deleteCredential(token, provider);
    return NextResponse.json({ result });
  } catch (error) {
    if (error instanceof ApiError && (error.status === 401 || error.status === 403)) {
      return NextResponse.json({ detail: "Admin role required" }, { status: error.status });
    }
    if (error instanceof ApiError && error.status === 404) {
      return NextResponse.json(
        { detail: "No active credential for this provider" },
        { status: 404 },
      );
    }
    return NextResponse.json({ detail: "Request failed" }, { status: 502 });
  }
}
