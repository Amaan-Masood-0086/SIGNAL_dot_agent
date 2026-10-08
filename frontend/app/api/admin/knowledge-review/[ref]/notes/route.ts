import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import { backendFetch, ApiError } from "@/src/lib/api/client";
import { reviewNoteSchema, reviewWriteSchema } from "@/src/lib/api/knowledge-review-schemas";
import { SESSION_COOKIE } from "@/src/lib/auth/constants";
import { isSameOrigin } from "@/src/lib/auth/csrf";
async function handle(request: NextRequest, ref: string, write: boolean) {
  if (write && !isSameOrigin(request)) return NextResponse.json({ detail: "Forbidden" }, { status: 403 });
  const token = request.cookies.get(SESSION_COOKIE)?.value;
  if (!token) return NextResponse.json({ detail: "Sign in again" }, { status: 401 });
  if (!/^V3-[A-Z]+-(?:M-)?[0-9]+(?:-[0-9]+)?$/.test(ref)) return NextResponse.json({ detail: "Invalid entry" }, { status: 400 });
  let body: string | undefined;
  if (write) {
    const parsed = reviewWriteSchema.safeParse(await request.json().catch(() => null));
    if (!parsed.success) return NextResponse.json({ detail: "Check the reviewer name, feedback and attachment size." }, { status: 422 });
    body = JSON.stringify(parsed.data);
  }
  try {
    const raw = await backendFetch(`/api/v1/admin/knowledge-review/${ref}/notes`, token, { method: write ? "POST" : "GET", body });
    const data = write ? z.object({ data: reviewNoteSchema }).parse(raw).data : z.object({ data: z.array(reviewNoteSchema) }).parse(raw).data;
    return NextResponse.json({ data }, { status: write ? 201 : 200 });
  } catch (error) {
    const status = error instanceof ApiError && [401,403,404,409,422,503].includes(error.status) ? error.status : 502;
    return NextResponse.json({ detail: status === 409 ? "Evidence or feedback changed. Reload this page before recording another review." : status === 403 ? "System administrator access required." : "Review feedback could not be loaded or saved. Your draft has not been cleared." }, { status });
  }
}
export async function GET(request: NextRequest, { params }: { params: Promise<{ ref: string }> }) { return handle(request, (await params).ref, false); }
export async function POST(request: NextRequest, { params }: { params: Promise<{ ref: string }> }) { return handle(request, (await params).ref, true); }
