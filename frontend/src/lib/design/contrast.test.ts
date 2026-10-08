import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";

// Design gate: every foreground/background pair the UI relies on must meet
// WCAG 2.2 AA, measured from the tokens in globals.css rather than a copy.
const css = readFileSync(path.resolve(__dirname, "../../../app/globals.css"), "utf8");
const root = css.match(/:root\s*\{([^}]*)\}/)?.[1] ?? "";
const token = (name: string): string => {
  const hex = root.match(new RegExp(`--${name}:[^#]*(#[0-9a-fA-F]{6})`))?.[1];
  if (!hex) throw new Error(`token --${name} not found in :root`);
  return hex;
};

const channel = (v: number) => (v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4);
const luminance = (hex: string) => {
  const [r, g, b] = [1, 3, 5].map((i) => channel(parseInt(hex.slice(i, i + 2), 16) / 255));
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
};
const ratio = (a: string, b: string) => {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (hi + 0.05) / (lo + 0.05);
};

const TEXT_PAIRS: [string, string][] = [
  ["ink", "surface"], ["ink", "paper"], ["ink-soft", "surface"], ["ink-soft", "paper"],
  ["pine", "surface"], ["pine", "paper"], ["surface", "pine"], ["surface", "pine-deep"],
  ["amber", "amber-soft"], ["amber", "paper"], ["red", "red-soft"], ["red", "paper"],
];

describe("design tokens meet WCAG 2.2 AA", () => {
  it.each(TEXT_PAIRS)("text %s on %s is at least 4.5:1", (fg, bg) => {
    expect(ratio(token(fg), token(bg))).toBeGreaterThanOrEqual(4.5);
  });

  it.each([["surface"], ["paper"]])("form-control border is at least 3:1 on %s", (bg) => {
    expect(ratio(token("control"), token(bg))).toBeGreaterThanOrEqual(3);
  });
});
