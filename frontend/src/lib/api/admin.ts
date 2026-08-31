// Server-only admin API functions (RBAC ticket + ADR-10 credentials).
// Zod-validated like every backend response (MUST #16). The credential
// schemas are deliberately value-less — the write-only contract means no
// response type even HAS a field that could carry a key.

import { backendFetch } from "@/src/lib/api/client";
import { z } from "zod";

export const providerStatusSchema = z.object({
  provider: z.enum(["stt", "llm"]),
  backend: z.string(),
  configured: z.boolean(),
  detail: z.string(),
  source: z.enum(["ui", "env"]).nullable(),
});
export type ProviderStatus = z.infer<typeof providerStatusSchema>;

const providerListEnvelopeSchema = z.object({
  success: z.boolean(),
  data: z.object({ providers: z.array(providerStatusSchema) }),
});

export const credentialStatusSchema = z.object({
  provider: z.string(),
  is_active: z.boolean(),
  masked_suffix: z.string().nullable(),
  updated_at: z.string().nullable(),
});
export type CredentialStatus = z.infer<typeof credentialStatusSchema>;

const credentialListEnvelopeSchema = z.object({
  success: z.boolean(),
  data: z.object({ providers: z.array(credentialStatusSchema) }),
});

const credentialWriteEnvelopeSchema = z.object({
  success: z.boolean(),
  data: credentialStatusSchema,
});

const providerTestEnvelopeSchema = z.object({
  success: z.boolean(),
  data: z.object({ provider: z.string(), success: z.boolean(), detail: z.string() }),
});

export async function listProviderStatuses(token: string): Promise<ProviderStatus[]> {
  const raw = await backendFetch<unknown>("/api/v1/admin/providers", token);
  return providerListEnvelopeSchema.parse(raw).data.providers;
}

export async function listCredentials(token: string): Promise<CredentialStatus[]> {
  const raw = await backendFetch<unknown>("/api/v1/admin/credentials", token);
  return credentialListEnvelopeSchema.parse(raw).data.providers;
}

export async function saveCredential(
  token: string,
  provider: string,
  value: string,
): Promise<CredentialStatus> {
  const raw = await backendFetch<unknown>(
    `/api/v1/admin/credentials/${provider}`,
    token,
    { method: "PUT", body: JSON.stringify({ value }) },
  );
  return credentialWriteEnvelopeSchema.parse(raw).data;
}

export async function deleteCredential(
  token: string,
  provider: string,
): Promise<CredentialStatus> {
  const raw = await backendFetch<unknown>(
    `/api/v1/admin/credentials/${provider}`,
    token,
    { method: "DELETE" },
  );
  return credentialWriteEnvelopeSchema.parse(raw).data;
}

export async function testProviderConnection(
  token: string,
  provider: string,
): Promise<{ provider: string; success: boolean; detail: string }> {
  const raw = await backendFetch<unknown>(
    `/api/v1/admin/providers/${provider}/test`,
    token,
    { method: "POST", body: "" },
  );
  return providerTestEnvelopeSchema.parse(raw).data;
}
