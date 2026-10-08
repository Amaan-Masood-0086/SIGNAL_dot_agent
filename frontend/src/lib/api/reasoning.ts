// Server-only reasoning API (FEAT-06 adaptive loop). Zod-validated like
// every other backend response (MUST #16).

import { backendFetch } from "@/src/lib/api/client";
import {
  reasoningEnvelopeSchema,
  reasoningResultSchema,
  type ReasoningInput,
  type ReasoningResult,
} from "@/src/lib/api/schemas";
import { z } from "zod";

export async function getSavedResult(token: string, sessionId: string): Promise<ReasoningResult | null> {
  return z.object({ data: reasoningResultSchema.nullable() }).parse(await backendFetch(`/api/v1/sessions/${sessionId}/result`, token)).data;
}

export async function reasonSession(
  token: string,
  sessionId: string,
  input: ReasoningInput,
): Promise<ReasoningResult> {
  const raw = await backendFetch<unknown>(
    `/api/v1/sessions/${sessionId}/reason`,
    token,
    { method: "POST", body: JSON.stringify(input) },
  );
  return reasoningEnvelopeSchema.parse(raw).data;
}
