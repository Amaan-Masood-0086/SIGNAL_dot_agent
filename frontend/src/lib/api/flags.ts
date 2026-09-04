// Server-only flags API (FEAT-09). Zod-validated like every backend
// response (MUST #16).

import { backendFetch } from "@/src/lib/api/client";
import {
  flagPageEnvelopeSchema,
  flagReadEnvelopeSchema,
  type FlagPage,
  type FlagRead,
} from "@/src/lib/api/schemas";

export async function listChildFlags(
  token: string,
  childId: string,
  page = 1,
  pageSize = 50,
): Promise<FlagPage> {
  const raw = await backendFetch<unknown>(
    `/api/v1/children/${childId}/flags?page=${page}&page_size=${pageSize}`,
    token,
  );
  return flagPageEnvelopeSchema.parse(raw).data;
}

/** One flag with its resolved reasoning trail (ADR-03/08: every displayed
 *  basis carries the knowledge-base row's description + source). Backend
 *  returns a uniform 403 for both missing and foreign flags (IDOR T2). */
export async function getFlag(token: string, flagId: string): Promise<FlagRead> {
  const raw = await backendFetch<unknown>(`/api/v1/flags/${flagId}`, token);
  return flagReadEnvelopeSchema.parse(raw).data;
}
