// Server-only session/observation API functions (FEAT-03). Responses are
// Zod-validated before any component sees them (MUST #16).

import { ApiError, backendFetch, backendFetchForm } from "@/src/lib/api/client";
import {
  observationEnvelopeSchema,
  observationPageEnvelopeSchema,
  sessionEnvelopeSchema,
  transcriptEnvelopeSchema,
  type Observation,
  type ObservationCreateInput,
  type ObservationPage,
  type Session,
  type SessionCreateInput,
  type Transcript,
} from "@/src/lib/api/schemas";

export async function createSession(
  token: string,
  input: SessionCreateInput,
): Promise<Session> {
  const raw = await backendFetch<unknown>("/api/v1/sessions", token, {
    method: "POST",
    body: JSON.stringify(input),
  });
  return sessionEnvelopeSchema.parse(raw).data;
}

export async function getSession(token: string, sessionId: string): Promise<Session> {
  const raw = await backendFetch<unknown>(`/api/v1/sessions/${sessionId}`, token);
  return sessionEnvelopeSchema.parse(raw).data;
}

export async function completeSession(token: string, sessionId: string): Promise<Session> {
  const raw = await backendFetch<unknown>(
    `/api/v1/sessions/${sessionId}/complete`,
    token,
    { method: "POST", body: "" },
  );
  return sessionEnvelopeSchema.parse(raw).data;
}

export async function addObservation(
  token: string,
  sessionId: string,
  input: ObservationCreateInput,
): Promise<Observation> {
  const raw = await backendFetch<unknown>(
    `/api/v1/sessions/${sessionId}/observations`,
    token,
    { method: "POST", body: JSON.stringify(input) },
  );
  return observationEnvelopeSchema.parse(raw).data;
}

export async function listObservations(
  token: string,
  sessionId: string,
  page = 1,
  pageSize = 50,
): Promise<ObservationPage> {
  const raw = await backendFetch<unknown>(
    `/api/v1/sessions/${sessionId}/observations?page=${page}&page_size=${pageSize}`,
    token,
  );
  return observationPageEnvelopeSchema.parse(raw).data;
}

// Voice mode only: send the recorded clip to the backend STT seam. The text
// path NEVER calls this — zero STT dependency is a FEAT-03 acceptance item.
export async function transcribeAudio(token: string, audio: Blob): Promise<Transcript> {
  const form = new FormData();
  form.append("audio", audio, "turn.webm");
  const raw = await backendFetchForm<unknown>("/api/v1/stt/transcribe", token, form);
  return transcriptEnvelopeSchema.parse(raw).data;
}

export function isAuthorizationError(error: unknown): boolean {
  return error instanceof ApiError && (error.status === 401 || error.status === 403);
}

export function isSttUnavailable(error: unknown): boolean {
  return error instanceof ApiError && error.status === 503;
}
