// Server-only flags API (FEAT-09). Zod-validated like every backend
// response (MUST #16).

import { backendFetch } from "@/src/lib/api/client";
import {
  flagPageEnvelopeSchema,
  type FlagPage,
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
