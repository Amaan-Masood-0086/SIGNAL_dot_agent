import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import { isSameOrigin } from "@/src/lib/auth/csrf";
import { SESSION_COOKIE } from "@/src/lib/auth/constants";
import { backendFetch, ApiError } from "./client";
import { referralCreate, referralUpdate, referralEnvelope } from "./referral-schemas";

export async function writeReferral(request: NextRequest, id: string, create: boolean) {
  if (!isSameOrigin(request)) return NextResponse.json({ detail: "Forbidden" }, { status: 403 });
  const token = request.cookies.get(SESSION_COOKIE)?.value;
  if (!token) return NextResponse.json({ detail: "Sign in again" }, { status: 401 });
  if (!z.uuid().safeParse(id).success) return NextResponse.json({ detail: "Invalid record" }, { status: 400 });
  const input = (create ? referralCreate : referralUpdate).safeParse(await request.json().catch(() => null));
  if (!input.success) return NextResponse.json({ detail: "Provide a responsible person, valid review date and required confirmation." }, { status: 422 });
  try {
    const raw = await backendFetch(create ? `/api/v1/flags/${id}/referral` : `/api/v1/referrals/${id}`, token, { method: create ? "POST" : "PATCH", body: JSON.stringify(input.data) });
    return NextResponse.json({ referral: referralEnvelope.parse(raw).data }, { status: create ? 201 : 200 });
  } catch (error) {
    const status = error instanceof ApiError && [401, 403, 409, 422].includes(error.status) ? error.status : 502;
    return NextResponse.json({ detail: status === 409 ? "An open referral already exists. Open the referral queue to review it." : status === 403 ? "You do not have access to this record." : "Referral could not be saved. Your entered details are still here." }, { status });
  }
}
