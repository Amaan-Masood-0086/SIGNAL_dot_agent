// SERVER-ONLY admin API functions (RBAC ticket + ADR-10 credentials).
// Import from route handlers and Server Components only — this module
// reaches the backend directly with the bearer token (MUST-NOT #12).
// Client components use `admin-client.ts`, which talks to the same-origin
// proxy routes instead.

import { backendFetch } from "@/src/lib/api/client";
import {
  auditPageEnvelopeSchema,
  chainEnvelopeSchema,
  childPageEnvelopeSchema,
  credentialListEnvelopeSchema,
  credentialWriteEnvelopeSchema,
  providerListEnvelopeSchema,
  providerTestEnvelopeSchema,
  staffPageEnvelopeSchema,
  usageEnvelopeSchema,
  type AdminChild,
  type AdminStaff,
  type AdminUsage,
  type AuditEntry,
  type ChainStatus,
  type CredentialStatus,
  type ProviderStatus,
} from "@/src/lib/api/admin-schemas";

export * from "@/src/lib/api/admin-schemas";

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
  model?: string | null,
): Promise<CredentialStatus> {
  const raw = await backendFetch<unknown>(
    `/api/v1/admin/credentials/${provider}`,
    token,
    { method: "PUT", body: JSON.stringify({ value, model: model ?? null }) },
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

export async function listStaff(
  token: string,
  page = 1,
): Promise<{ items: AdminStaff[]; total: number }> {
  const raw = await backendFetch<unknown>(
    `/api/v1/admin/staff?page=${page}&page_size=25`,
    token,
  );
  return staffPageEnvelopeSchema.parse(raw).data;
}

export async function listAllChildren(
  token: string,
  page = 1,
): Promise<{ items: AdminChild[]; total: number }> {
  const raw = await backendFetch<unknown>(
    `/api/v1/admin/children?page=${page}&page_size=25`,
    token,
  );
  return childPageEnvelopeSchema.parse(raw).data;
}

export async function listAuditLog(
  token: string,
  page = 1,
  action?: string,
): Promise<{ items: AuditEntry[]; total: number }> {
  const qs = new URLSearchParams({ page: String(page), page_size: "25" });
  if (action) qs.set("action", action);
  const raw = await backendFetch<unknown>(`/api/v1/audit_log?${qs.toString()}`, token);
  return auditPageEnvelopeSchema.parse(raw).data;
}

export async function getAuditChainStatus(token: string): Promise<ChainStatus> {
  const raw = await backendFetch<unknown>("/api/v1/audit_log/integrity", token);
  return chainEnvelopeSchema.parse(raw).data;
}

export async function getAllUsage(token: string): Promise<AdminUsage> {
  const raw = await backendFetch<unknown>("/api/v1/admin/usage", token);
  return usageEnvelopeSchema.parse(raw).data;
}
