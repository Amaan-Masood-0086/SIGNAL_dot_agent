import { NextRequest, NextResponse } from "next/server";
import { getSessionToken } from "@/src/lib/auth/session";

export async function POST(request: NextRequest) {
  const token = await getSessionToken();
  if (!token) return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
  const base = process.env.BACKEND_URL ?? "http://localhost:8000";
  const response = await fetch(`${base}/api/v1/admin/knowledge/preview`, {
    method: "POST", headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify(await request.json()), cache: "no-store",
  });
  return NextResponse.json(await response.json(), { status: response.status });
}
