import { z } from "zod";
export const referralStatus = z.enum(["referred", "pending_capacity", "closed"]);
export const referralFields = z.object({
  responsible_person: z.string().trim().min(1).max(200),
  review_date: z.iso.date(),
});
export const referralCreate = referralFields.extend({ caretaker_confirmed: z.literal(true) });
export const referralUpdate = referralFields.extend({ status: referralStatus });
export const referralRead = z.object({
  id: z.uuid(), flag_id: z.uuid(), status: referralStatus,
  responsible_person: z.string().nullable(), review_date: z.string().nullable(),
  escalated: z.boolean(), caretaker_confirmed: z.boolean(), created_at: z.string(),
});
export const referralEnvelope = z.object({ data: referralRead });
export const referralPageEnvelope = z.object({ data: z.object({ items: z.array(referralRead), total: z.number().int().nonnegative(), page: z.number().int().positive(), page_size: z.number().int().positive() }) });
export type Referral = z.infer<typeof referralRead>;
