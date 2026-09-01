// Browser-side admin calls. Every request goes to a SAME-ORIGIN proxy route
// under /api/admin/* — the bearer token stays in the HttpOnly cookie and is
// attached server-side, so no token ever reaches this file.
//
// Responses are Zod-parsed here too: a proxy is not a trust boundary.

import {
  auditPageEnvelopeSchema,
  chainEnvelopeSchema,
  childPageEnvelopeSchema,
  credentialListEnvelopeSchema,
  credentialStatusSchema,
  providerListEnvelopeSchema,
  providerTestResultSchema,
  staffEnvelopeSchema,
  staffPageEnvelopeSchema,
  usageEnvelopeSchema,
  type AdminChild,
  type AdminStaff,
  type AdminUsage,
  type AuditEntry,
  type ChainStatus,
  type CredentialStatus,
  type ProviderStatus,
  type ProviderTestResult,
} from "@/src/lib/api/admin-schemas";

/** Thrown with the proxy's generic, non-internal message (MUST-NOT #16). */
export class AdminRequestError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = "AdminRequestError";
  }
}

async function request<T>(
  path: string,
  init: RequestInit,
  parse: (raw: unknown) => T,
): Promise<T> {
  let response: Response;
  try {
    response = await fetch(path, { ...init, cache: "no-store" });
  } catch {
    throw new AdminRequestError(0, "Network unavailable — check your connection.");
  }

  let payload: unknown = null;
  try {
    payload = await response.json();
  } catch {
    payload = null;
  }

  if (!response.ok) {
    const detail =
      payload && typeof payload === "object" && "detail" in payload
        ? String((payload as { detail: unknown }).detail)
        : "Request failed";
    throw new AdminRequestError(response.status, detail);
  }
  return parse(payload);
}

const jsonInit = (method: string, body: unknown): RequestInit => ({
  method,
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body),
});

// ── Providers & credentials ────────────────────────────────────────────

export function fetchProviderStatuses(): Promise<ProviderStatus[]> {
  return request("/api/admin/providers", {}, (raw) =>
    providerListEnvelopeSchema.parse({ success: true, data: raw }).data.providers,
  );
}

export function fetchCredentials(): Promise<CredentialStatus[]> {
  return request("/api/admin/credentials", {}, (raw) =>
    credentialListEnvelopeSchema.parse({ success: true, data: raw }).data.providers,
  );
}

export function saveCredential(
  provider: string,
  value: string,
  model?: string | null,
): Promise<CredentialStatus> {
  return request(
    `/api/admin/credentials/${provider}`,
    jsonInit("PUT", { value, model: model ?? null }),
    (raw) => credentialStatusSchema.parse((raw as { result: unknown }).result),
  );
}

export function deleteCredential(provider: string): Promise<CredentialStatus> {
  return request(`/api/admin/credentials/${provider}`, { method: "DELETE" }, (raw) =>
    credentialStatusSchema.parse((raw as { result: unknown }).result),
  );
}

export function testProvider(provider: string): Promise<ProviderTestResult> {
  return request(`/api/admin/providers/${provider}/test`, { method: "POST" }, (raw) =>
    providerTestResultSchema.parse((raw as { result: unknown }).result),
  );
}

// ── Staff ──────────────────────────────────────────────────────────────

export function fetchStaff(page = 1): Promise<{ items: AdminStaff[]; total: number }> {
  return request(
    `/api/admin/staff?page=${page}`,
    {},
    (raw) => staffPageEnvelopeSchema.parse(raw).data,
  );
}

export function updateStaffRole(staffId: string, role: string): Promise<AdminStaff> {
  return request(
    `/api/admin/staff/${staffId}/role`,
    jsonInit("PATCH", { role }),
    (raw) => staffEnvelopeSchema.parse(raw).data,
  );
}

export function updateStaffActive(staffId: string, isActive: boolean): Promise<AdminStaff> {
  return request(
    `/api/admin/staff/${staffId}/active`,
    jsonInit("PATCH", { is_active: isActive }),
    (raw) => staffEnvelopeSchema.parse(raw).data,
  );
}

// ── Children / audit / usage ───────────────────────────────────────────

export function fetchAllChildren(
  page = 1,
): Promise<{ items: AdminChild[]; total: number }> {
  return request(
    `/api/admin/children?page=${page}`,
    {},
    (raw) => childPageEnvelopeSchema.parse(raw).data,
  );
}

export function fetchAuditLog(
  page = 1,
  action?: string,
): Promise<{ items: AuditEntry[]; total: number }> {
  const qs = new URLSearchParams({ page: String(page) });
  if (action) qs.set("action", action);
  return request(
    `/api/admin/audit?${qs.toString()}`,
    {},
    (raw) => auditPageEnvelopeSchema.parse(raw).data,
  );
}

export function fetchChainStatus(): Promise<ChainStatus> {
  return request("/api/admin/audit/integrity", {}, (raw) =>
    chainEnvelopeSchema.parse(raw).data,
  );
}

export function fetchUsage(): Promise<AdminUsage> {
  return request("/api/admin/usage", {}, (raw) => usageEnvelopeSchema.parse(raw).data);
}
