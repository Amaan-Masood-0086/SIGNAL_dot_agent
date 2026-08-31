// Server-only child API functions (FEAT-02). Responses are Zod-validated
// before any component sees them (MUST #16).

import { ApiError, backendFetch } from "@/src/lib/api/client";
import {
  childEnvelopeSchema,
  childPageEnvelopeSchema,
  type Child,
  type ChildCreateInput,
  type ChildPage,
} from "@/src/lib/api/schemas";

export async function listChildren(
  token: string,
  page = 1,
  pageSize = 50,
): Promise<ChildPage> {
  const raw = await backendFetch<unknown>(
    `/api/v1/children?page=${page}&page_size=${pageSize}`,
    token,
  );
  return childPageEnvelopeSchema.parse(raw).data;
}

export async function createChild(
  token: string,
  input: ChildCreateInput,
): Promise<Child> {
  const raw = await backendFetch<unknown>("/api/v1/children", token, {
    method: "POST",
    body: JSON.stringify(input),
  });
  return childEnvelopeSchema.parse(raw).data;
}

export async function getChild(token: string, childId: string): Promise<Child> {
  const raw = await backendFetch<unknown>(`/api/v1/children/${childId}`, token);
  return childEnvelopeSchema.parse(raw).data;
}

export function isAuthorizationError(error: unknown): boolean {
  return error instanceof ApiError && (error.status === 401 || error.status === 403);
}
