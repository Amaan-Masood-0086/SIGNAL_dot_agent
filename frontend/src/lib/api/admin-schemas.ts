// Isomorphic admin response schemas — safe to import from BOTH server code
// and client components. Deliberately free of any transport concern so the
// server-only fetch wrapper (`client.ts`, which reads BACKEND_URL) never
// gets pulled into a browser bundle.
//
// ADR-09/10 write-only contract: no schema here has a field that could
// carry key material. Masking is structural, not cosmetic.

import { z } from "zod";

export const providerStatusSchema = z.object({
  provider: z.enum(["stt", "llm"]),
  backend: z.string(),
  configured: z.boolean(),
  detail: z.string(),
  source: z.enum(["ui", "env"]).nullable(),
});
export type ProviderStatus = z.infer<typeof providerStatusSchema>;

export const providerListEnvelopeSchema = z.object({
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

export const credentialListEnvelopeSchema = z.object({
  success: z.boolean(),
  data: z.object({ providers: z.array(credentialStatusSchema) }),
});

export const credentialWriteEnvelopeSchema = z.object({
  success: z.boolean(),
  data: credentialStatusSchema,
});

export const providerTestResultSchema = z.object({
  provider: z.string(),
  success: z.boolean(),
  detail: z.string(),
});
export type ProviderTestResult = z.infer<typeof providerTestResultSchema>;

export const providerTestEnvelopeSchema = z.object({
  success: z.boolean(),
  data: providerTestResultSchema,
});

export const adminStaffSchema = z.object({
  id: z.string(),
  institution_id: z.string(),
  email: z.string(),
  role: z.string(),
  is_active: z.boolean(),
  created_at: z.string(),
});
export type AdminStaff = z.infer<typeof adminStaffSchema>;

export const staffPageEnvelopeSchema = z.object({
  success: z.boolean(),
  data: z.object({ items: z.array(adminStaffSchema), total: z.number() }),
});
export const staffEnvelopeSchema = z.object({
  success: z.boolean(),
  data: adminStaffSchema,
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

export const childPageEnvelopeSchema = z.object({
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

export const auditPageEnvelopeSchema = z.object({
  success: z.boolean(),
  data: z.object({ items: z.array(auditEntrySchema), total: z.number() }),
});

export const chainStatusSchema = z.object({
  chain_intact: z.boolean(),
  entries_checked: z.number(),
  first_broken_sequence: z.number().nullable(),
});
export type ChainStatus = z.infer<typeof chainStatusSchema>;

export const chainEnvelopeSchema = z.object({
  success: z.boolean(),
  data: chainStatusSchema,
});

// `estimated_cost` is null for "not recorded", NOT zero — an LLM test
// connection is a real billed call whose price cannot be computed, while an
// STT provider test genuinely costs nothing and records 0. `unpriced_calls`
// covers the mixed case: SUM skips nulls, so a partial total would otherwise
// read as a complete bill.
const usageTotalsSchema = z.object({
  calls: z.number(),
  estimated_cost: z.number().nullable(),
  unpriced_calls: z.number(),
});

export const usageEnvelopeSchema = z.object({
  success: z.boolean(),
  data: z.object({
    total: usageTotalsSchema,
    // STT and LLM are separate vendors with separate invoices; a merged
    // figure reconciles against neither.
    by_provider: z.object({
      stt: usageTotalsSchema,
      llm: usageTotalsSchema,
    }),
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

// Page size the admin proxies request. Kept here so the client's
// "is there a next page?" logic can never drift from the proxy.
export const ADMIN_PAGE_SIZE = 25;
