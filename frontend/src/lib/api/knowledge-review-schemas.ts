import { z } from "zod";
export const reviewStatus = z.enum(["pending", "changes_requested", "reviewed"]);
const sourceSchema = z.object({ source_id: z.string(), title: z.string(), url: z.url().refine(url => url.startsWith("https://")), locator: z.string(), limitations: z.string() });
export const reviewEntrySchema = z.object({
  citation_ref: z.string(), content_sha256: z.string(), workflow_status: reviewStatus,
  feedback_stale: z.boolean(), latest_note_id: z.number().int().nonnegative(),
  snapshot: z.object({ sources: z.array(sourceSchema), entry: z.object({
    domain: z.string(), entry_kind: z.string(), observation: z.string(),
    age_min_months: z.number(), age_max_months_exclusive: z.number(), age_semantics: z.string(), age_basis: z.string(),
    follow_up_en: z.string(), follow_up_ur_latn: z.string(), interpretation_notes: z.string(), evidence_group: z.string(),
  }) }),
});
export const reviewCatalogSchema = z.object({ release_id: z.string(), runtime_enabled: z.literal(false), items: z.array(reviewEntrySchema) });
export const reviewWriteSchema = z.object({
  content_sha256: z.string().regex(/^[0-9a-f]{64}$/), expected_note_id: z.number().int().nonnegative(),
  status: reviewStatus, reviewer_name: z.string().trim().min(1).max(200), feedback: z.string().trim().min(1).max(10000),
  attachment_name: z.string().max(200).nullable().optional(), attachment_text: z.string().max(32000).nullable().optional(),
}).strict();
export const reviewNoteSchema = z.object({ id: z.number(), citation_ref: z.string(), content_sha256: z.string(), status: reviewStatus, reviewer_name: z.string(), feedback: z.string(), attachment_name: z.string().nullable(), attachment_text: z.string().nullable(), recorded_by: z.string(), created_at: z.string() });
export type ReviewEntry = z.infer<typeof reviewEntrySchema>;
export type ReviewCatalog = z.infer<typeof reviewCatalogSchema>;
export type ReviewNote = z.infer<typeof reviewNoteSchema>;
