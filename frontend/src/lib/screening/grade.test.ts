import { describe, expect, it } from "vitest";

import { domainLabel, gradeBadgeTone, gradeMeta, normalizeGrade } from "./grade";

/**
 * Grade labelling is clinical copy, not decoration.
 *
 * Two surfaces deliver a grade in different casing — the live reasoning
 * result carries knowledge.py's uppercase constants, a persisted flag carries
 * the DB enum's lowercase form. Each screen used to keep its own map keyed to
 * its own casing, so a grade shown on the wrong screen fell through to the
 * raw string. These tests pin the normaliser that replaced both maps.
 */
describe("normalizeGrade", () => {
  it("accepts the live reasoning casing", () => {
    expect(normalizeGrade("HIGH")).toBe("high");
    expect(normalizeGrade("LOW_MONITOR")).toBe("low_monitor");
    expect(normalizeGrade("INSUFFICIENT_INFORMATION")).toBe("insufficient_information");
  });

  it("accepts the persisted-flag casing", () => {
    expect(normalizeGrade("high")).toBe("high");
    expect(normalizeGrade("moderate")).toBe("moderate");
  });

  it("returns null rather than guessing at an unknown grade", () => {
    expect(normalizeGrade("catastrophic")).toBeNull();
    expect(normalizeGrade(null)).toBeNull();
    expect(normalizeGrade(undefined)).toBeNull();
    expect(normalizeGrade("")).toBeNull();
  });
});

describe("gradeMeta", () => {
  it("labels all four ADR-06 grades in both casings", () => {
    for (const grade of ["HIGH", "MODERATE", "LOW_MONITOR", "INSUFFICIENT_INFORMATION"]) {
      expect(gradeMeta(grade), grade).not.toBeNull();
      expect(gradeMeta(grade.toLowerCase()), grade).toEqual(gradeMeta(grade));
    }
  });

  it("never phrases a grade as a diagnosis (ADR-07)", () => {
    const banned = /\b(diagnos|disorder|confirmed case|has autism|is deaf)\b/i;
    for (const grade of ["high", "moderate", "low_monitor", "insufficient_information"]) {
      const meta = gradeMeta(grade)!;
      expect(banned.test(meta.headline), `headline: ${meta.headline}`).toBe(false);
      expect(banned.test(meta.meaning), `meaning: ${meta.meaning}`).toBe(false);
    }
  });

  it("does not present insufficient information as reassuring (ADR-06 sub-rule 2)", () => {
    const meta = gradeMeta("insufficient_information")!;
    // The copy must say so explicitly. A keyword blocklist is the wrong tool
    // here — the real wording is "…not that the child is fine", where the
    // reassuring word appears precisely because it is being negated.
    expect(meta.meaning).toMatch(/not a reassuring result/i);
    expect(meta.headline).toMatch(/repeat the check/i);
  });

  it("escalates tone with severity", () => {
    expect(gradeMeta("high")!.tone).toBe("danger");
    expect(gradeMeta("moderate")!.tone).toBe("warning");
    expect(gradeMeta("low_monitor")!.tone).toBe("pine");
  });
});

describe("gradeBadgeTone", () => {
  it("maps onto the tones the Badge primitive actually has", () => {
    // Badge has no "pine" tone; low_monitor must degrade to neutral, not crash.
    expect(gradeBadgeTone("HIGH")).toBe("danger");
    expect(gradeBadgeTone("moderate")).toBe("warning");
    expect(gradeBadgeTone("low_monitor")).toBe("neutral");
    expect(gradeBadgeTone("nonsense")).toBe("neutral");
  });
});

describe("domainLabel", () => {
  it("renders the stored domain keys as human labels", () => {
    expect(domainLabel("Speech_Language")).toBe("Speech & language");
    expect(domainLabel("Hearing")).toBe("Hearing");
  });

  it("passes an unknown domain through instead of blanking it", () => {
    expect(domainLabel("Motor")).toBe("Motor");
    expect(domainLabel(null)).toBeNull();
  });
});
