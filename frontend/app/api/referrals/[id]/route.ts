import type { NextRequest } from "next/server";
import { writeReferral } from "@/src/lib/api/referral-write";
export async function PATCH(request: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  return writeReferral(request, (await params).id, false);
}
