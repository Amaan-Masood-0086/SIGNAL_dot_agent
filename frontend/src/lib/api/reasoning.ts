// Server-only reasoning API (FEAT-06 adaptive loop). Zod-validated like
// every other backend response (MUST #16).

import { backendFetch } from "@/src/lib/api/client";
import {
  reasoningEnvelopeSchema,
  type ReasoningInput,
  type ReasoningResult,
} from "@/src/lib/api/schemas";

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
