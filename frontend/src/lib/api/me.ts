// Server-only identity fetch. `/auth/me` is the ONLY place the frontend
// learns the caller's role — never a client-supplied value, never a claim
// decoded in the browser.

import { backendFetch } from "@/src/lib/api/client";
import { z } from "zod";

export const meSchema = z.object({
  staff_id: z.string(),
  institution_id: z.string(),
  role: z.enum(["caretaker", "admin"]),
  email: z.string().nullable(),
  institution_name: z.string().nullable(),
  is_admin: z.boolean(),
});
export type Me = z.infer<typeof meSchema>;

const meEnvelopeSchema = z.object({ success: z.boolean(), data: meSchema });

export async function getMe(token: string): Promise<Me> {
  const raw = await backendFetch<unknown>("/api/v1/auth/me", token);
  return meEnvelopeSchema.parse(raw).data;
}
