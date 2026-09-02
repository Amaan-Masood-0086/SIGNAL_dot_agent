/**
 * The four ADR-06 confidence grades, in one place.
 *
 * The two surfaces that display a grade receive it in different casing: the
 * live reasoning result carries knowledge.py's uppercase constants ("HIGH"),
 * while a persisted flag carries the DB enum's lowercase form ("high"). Both
 * screens used to keep their own label map keyed to their own casing, so a
 * wording change had to be made twice and a grade rendered on the wrong
 * screen fell through to the raw string. Normalise once, label once.
 *
 * The wording here is clinical copy, not decoration: ADR-07 forbids
 * presenting any of this as a diagnosis, and INSUFFICIENT_INFORMATION is
 * explicitly NOT a reassuring outcome (ADR-06 sub-rule 2).
 */

export type Grade = "high" | "moderate" | "low_monitor" | "insufficient_information";

export type GradeTone = "danger" | "warning" | "pine" | "neutral";

export interface GradeMeta {
  /** Short label for chips and table cells. */
  label: string;
  /** The recommended action, as a sentence — the actual output of screening. */
  headline: string;
  /** Why this grade was reached / what it does and does not mean. */
  meaning: string;
  tone: GradeTone;
}

const GRADES: Record<Grade, GradeMeta> = {
  high: {
    label: "High",
    headline: "See a clinician soon",
    meaning:
      "The pattern described matches milestones that are usually met by this age. This is a referral prompt, not a diagnosis.",
    tone: "danger",
  },
  moderate: {
    label: "Moderate",
    headline: "Have it checked",
    meaning:
      "Enough of a signal to warrant a professional check, without the urgency of a high grade.",
    tone: "warning",
  },
  low_monitor: {
    label: "Low",
    headline: "Monitor and recheck",
    meaning:
      "Nothing here calls for referral today. Recheck if the picture changes, or at the next routine review.",
    tone: "pine",
  },
  insufficient_information: {
    label: "Not enough information",
    headline: "Repeat the check with someone who knows the child daily",
    meaning:
      "This is not a reassuring result. It means the answers so far cannot support any grade — not that the child is fine.",
    tone: "neutral",
  },
};

/** Accepts either casing; returns null for anything unrecognised. */
export function normalizeGrade(grade: string | null | undefined): Grade | null {
  if (!grade) return null;
  const key = grade.toLowerCase();
  return key in GRADES ? (key as Grade) : null;
}

export function gradeMeta(grade: string | null | undefined): GradeMeta | null {
  const key = normalizeGrade(grade);
  return key ? GRADES[key] : null;
}

/** Badge tone for the shared Badge primitive (which has no "pine" tone). */
export function gradeBadgeTone(
  grade: string | null | undefined,
): "danger" | "warning" | "neutral" {
  const tone = gradeMeta(grade)?.tone;
  if (tone === "danger") return "danger";
  if (tone === "warning") return "warning";
  return "neutral";
}

export function domainLabel(domain: string | null | undefined): string | null {
  if (!domain) return null;
  if (domain === "Speech_Language") return "Speech & language";
  if (domain === "Hearing") return "Hearing";
  return domain;
}
