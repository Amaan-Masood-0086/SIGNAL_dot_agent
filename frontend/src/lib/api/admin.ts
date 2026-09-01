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
  model_name: z.string().nullable(),
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
  model?: string,
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

// ── Admin console: staff / children / audit / usage ────────────────────

export const adminStaffSchema = z.object({
  id: z.string(),
  institution_id: z.string(),
  email: z.string(),
  role: z.string(),
  is_active: z.boolean(),
  created_at: z.string(),
});
export type AdminStaff = z.infer<typeof adminStaffSchema>;

const staffPageEnvelopeSchema = z.object({
  success: z.boolean(),
  data: z.object({ items: z.array(adminStaffSchema), total: z.number() }),
});

export const adminChildSchema = z.object({
  id: z.string(),
  name: z.string(),
  institution_id: z.string(),
  institution_name: z.string(),
  dob_confirmed: z.boolean(),
  dob: z.string().nullable(),
  estimated_age_range: z.string().nullable(),
  intake_date: z.string(),
});
export type AdminChild = z.infer<typeof adminChildSchema>;

const childPageEnvelopeSchema = z.object({
  success: z.boolean(),
  data: z.object({ items: z.array(adminChildSchema), total: z.number() }),
});

export const auditEntrySchema = z.object({
  id: z.string(),
  sequence: z.number(),
  actor_id: z.string().nullable(),
  institution_id: z.string().nullable(),
  action: z.string(),
  resource_type: z.string(),
  resource_id: z.string(),
  timestamp: z.string(),
});
export type AuditEntry = z.infer<typeof auditEntrySchema>;

const auditPageEnvelopeSchema = z.object({
  success: z.boolean(),
  data: z.object({ items: z.array(auditEntrySchema), total: z.number() }),
});

export const chainStatusSchema = z.object({
  chain_intact: z.boolean(),
  entries_checked: z.number(),
  first_broken_sequence: z.number().nullable(),
});
export type ChainStatus = z.infer<typeof chainStatusSchema>;

const chainEnvelopeSchema = z.object({ success: z.boolean(), data: chainStatusSchema });

const usageEnvelopeSchema = z.object({
  success: z.boolean(),
  data: z.object({
    total: z.object({ calls: z.number(), estimated_cost: z.number().nullable() }),
    by_staff: z.array(
      z.object({
        staff_id: z.string(),
        email: z.string(),
        institution_id: z.string(),
        calls: z.number(),
        estimated_cost: z.number().nullable(),
      }),
    ),
    by_institution: z.array(
      z.object({
        institution_id: z.string(),
        name: z.string(),
        calls: z.number(),
        estimated_cost: z.number().nullable(),
      }),
    ),
  }),
});
export type AdminUsage = z.infer<typeof usageEnvelopeSchema>["data"];

export async function listAdminStaff(page = 1): Promise<{ items: AdminStaff[]; total: number }> {
  const resp = await fetch(`/api/admin/staff?page=${page}`);
  if (!resp.ok) throw new Error("staff list failed");
  return staffPageEnvelopeSchema.parse(await resp.json()).data;
}

export async function updateStaffRole(staffId: string, role: string): Promise<AdminStaff> {
  const resp = await fetch(`/api/admin/staff/${staffId}/role`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ role }),
  });
  if (!resp.ok) throw new Error((await resp.json()).detail ?? "role change failed");
  return z.object({ success: z.boolean(), data: adminStaffSchema }).parse(await resp.json()).data;
}

export async function updateStaffActive(staffId: string, isActive: boolean): Promise<AdminStaff> {
  const resp = await fetch(`/api/admin/staff/${staffId}/active`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ is_active: isActive }),
  });
  if (!resp.ok) throw new Error((await resp.json()).detail ?? "active change failed");
  return z.object({ success: z.boolean(), data: adminStaffSchema }).parse(await resp.json()).data;
}

export async function listAdminChildren(page = 1): Promise<{ items: AdminChild[]; total: number }> {
  const resp = await fetch(`/api/admin/children?page=${page}`);
  if (!resp.ok) throw new Error("children list failed");
  return childPageEnvelopeSchema.parse(await resp.json()).data;
}

export async function listAudit(
  params: { page?: number; action?: string } = {},
): Promise<{ items: AuditEntry[]; total: number }> {
  const qs = new URLSearchParams({ page: String(params.page ?? 1) });
  if (params.action) qs.set("action", params.action);
  const resp = await fetch(`/api/admin/audit?${qs.toString()}`);
  if (!resp.ok) throw new Error("audit list failed");
  return auditPageEnvelopeSchema.parse(await resp.json()).data;
}

export async function getChainStatus(): Promise<ChainStatus> {
  const resp = await fetch("/api/admin/audit/integrity");
  if (!resp.ok) throw new Error("integrity check failed");
  return chainEnvelopeSchema.parse(await resp.json()).data;
}

export async function listAdminUsage(): Promise<AdminUsage> {
  const resp = await fetch("/api/admin/usage");
  if (!resp.ok) throw new Error("usage list failed");
  return usageEnvelopeSchema.parse(await resp.json()).data;
}
