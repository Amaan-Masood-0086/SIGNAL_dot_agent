import { z } from "zod";

// Zod schemas for API shapes (web-development.md Step 4, MUST #16 — API
// response shapes are validated, never trusted). This file is client-safe:
// pure schemas only, no server-only imports (MUST-NOT #12).

export const envelopeMetaSchema = z.object({
  request_id: z.string(),
  timestamp: z.string(),
  version: z.string(),
});

export const childSchema = z.object({
  id: z.string().uuid(),
  institution_id: z.string().uuid(),
  name: z.string().min(1),
  intake_date: z.string(),
  dob_confirmed: z.boolean(),
  dob: z.string().nullable(),
  estimated_age_range: z.string().nullable(),
  estimated_age_note: z.string().nullable(),
  is_synthetic: z.boolean(),
  created_at: z.string(),
});

export type Child = z.infer<typeof childSchema>;

export const childEnvelopeSchema = z.object({
  success: z.boolean(),
  data: childSchema,
  meta: envelopeMetaSchema,
});

export const childPageSchema = z.object({
  items: z.array(childSchema),
  total: z.number().int().nonnegative(),
  page: z.number().int().positive(),
  page_size: z.number().int().positive(),
});

export type ChildPage = z.infer<typeof childPageSchema>;

export const childPageEnvelopeSchema = z.object({
  success: z.boolean(),
  data: childPageSchema,
  meta: envelopeMetaSchema,
});

// ADR-02 dual-age intake contract — mirrors the backend Pydantic validator
// so client-side validation (MUST #5) matches the server contract exactly.
export const childCreateSchema = z
  .object({
    name: z.string().trim().min(1, "Name is required").max(200),
    intake_date: z.string().optional(),
    dob_confirmed: z.boolean(),
    dob: z.string().nullable().optional(),
    estimated_age_range: z.string().max(50).nullable().optional(),
    estimated_age_note: z.string().nullable().optional(),
  })
  .superRefine((value, ctx) => {
    if (value.dob_confirmed) {
      if (!value.dob) {
        ctx.addIssue({
          code: "custom",
          path: ["dob"],
          message: "Date of birth is required when it is confirmed",
        });
      }
      if (value.estimated_age_range || value.estimated_age_note) {
        ctx.addIssue({
          code: "custom",
          path: ["estimated_age_range"],
          message: "Leave estimated-age fields empty for a confirmed DOB",
        });
      }
    } else {
      if (!value.estimated_age_range) {
        ctx.addIssue({
          code: "custom",
          path: ["estimated_age_range"],
          message: "Estimated age range is required when DOB is not confirmed",
        });
      }
      if (value.dob) {
        ctx.addIssue({
          code: "custom",
          path: ["dob"],
          message: "Do not enter a DOB when the age is estimated",
        });
      }
    }
  });

export type ChildCreateInput = z.infer<typeof childCreateSchema>;

// ── FEAT-03: sessions + observations (voice + text input layer) ──────────

export const sessionCreateSchema = z.object({
  child_id: z.string().uuid(),
  mode: z.enum(["voice", "text"]),
});

export type SessionCreateInput = z.infer<typeof sessionCreateSchema>;

export const sessionSchema = z.object({
  id: z.string().uuid(),
  institution_id: z.string().uuid(),
  child_id: z.string().uuid(),
  staff_id: z.string().uuid(),
  status: z.enum(["in_progress", "completed", "abandoned"]),
  mode: z.enum(["voice", "text"]),
  started_at: z.string(),
  resumed_at: z.string().nullable(),
  created_at: z.string(),
});

export type Session = z.infer<typeof sessionSchema>;

export const sessionEnvelopeSchema = z.object({
  success: z.boolean(),
  data: sessionSchema,
  meta: envelopeMetaSchema,
});

// FEAT-06: adaptive follow-up loop outcome for one reasoning turn.
export const reasoningInputSchema = z.object({
  raw_input: z.string().trim().min(1).max(10_000),
});
export type ReasoningInput = z.infer<typeof reasoningInputSchema>;

export const reasoningResultSchema = z.object({
  status: z.enum(["follow_up", "flagged", "insufficient_information", "safeguarding_escalation"]),
  turn: z.number().int().min(1),
  max_turns: z.number().int().min(1),
  follow_up_question: z.string().nullable(),
  grade: z.string().nullable(),
  domain: z.string().nullable(),
  citations: z.array(z.string()),
  explanation_text: z.string().nullable(),
  age_uncertain: z.boolean(),
  loop_exhausted: z.boolean(),
  flag_id: z.string().nullable(),
});
export type ReasoningResult = z.infer<typeof reasoningResultSchema>;

export const reasoningEnvelopeSchema = z.object({
  success: z.boolean(),
  data: reasoningResultSchema,
  meta: envelopeMetaSchema,
});

// FEAT-09: confidence-graded flag with a RESOLVED reasoning trail — every
// entry carries the knowledge-base row's description + source so a
// clinician can independently review the basis (ADR-03/08).
export const trailEntryReadSchema = z.object({
  citation_ref: z.string(),
  basis: z.string().nullable(),
  description: z.string().nullable(),
  source: z.string().nullable(),
});

export const flagReadSchema = z.object({
  id: z.string(),
  session_id: z.string(),
  child_id: z.string(),
  domain: z.string(),
  confidence_grade: z.string(),
  status: z.string(),
  explanation_text: z.string().nullable(),
  created_at: z.string(),
  reasoning_trail: z.array(trailEntryReadSchema),
});
export type FlagRead = z.infer<typeof flagReadSchema>;

export const flagPageSchema = z.object({
  items: z.array(flagReadSchema),
  total: z.number().int().min(0),
  page: z.number().int().min(1),
  page_size: z.number().int().min(1),
});
export type FlagPage = z.infer<typeof flagPageSchema>;

export const flagPageEnvelopeSchema = z.object({
  success: z.boolean(),
  data: flagPageSchema,
  meta: envelopeMetaSchema,
});

// Mode-agnostic observation: voice transcripts and typed text share this
// exact shape (FEAT-03 acceptance — identical downstream format).
export const observationCreateSchema = z.object({
  raw_input: z.string().trim().min(1, "Input is required").max(10_000),
});

export type ObservationCreateInput = z.infer<typeof observationCreateSchema>;

export const observationSchema = z.object({
  id: z.string().uuid(),
  institution_id: z.string().uuid(),
  session_id: z.string().uuid(),
  turn_number: z.number().int().positive(),
  raw_input: z.string(),
  extracted_signals: z.record(z.string(), z.unknown()).nullable(),
  created_at: z.string(),
});

export type Observation = z.infer<typeof observationSchema>;

export const observationEnvelopeSchema = z.object({
  success: z.boolean(),
  data: observationSchema,
  meta: envelopeMetaSchema,
});

export const observationPageSchema = z.object({
  items: z.array(observationSchema),
  total: z.number().int().nonnegative(),
  page: z.number().int().positive(),
  page_size: z.number().int().positive(),
});

export type ObservationPage = z.infer<typeof observationPageSchema>;

export const observationPageEnvelopeSchema = z.object({
  success: z.boolean(),
  data: observationPageSchema,
  meta: envelopeMetaSchema,
});

export const transcriptSchema = z.object({
  transcript: z.string(),
  language: z.string(),
});

export type Transcript = z.infer<typeof transcriptSchema>;

export const transcriptEnvelopeSchema = z.object({
  success: z.boolean(),
  data: transcriptSchema,
  meta: envelopeMetaSchema,
});
