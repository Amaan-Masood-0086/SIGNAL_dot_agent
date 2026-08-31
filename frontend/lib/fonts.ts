import { Bricolage_Grotesque, Noto_Sans } from "next/font/google";

// Self-hosted via next/font (no runtime request to third parties — CSP
// stays clean). Bricolage Grotesque is the display face (wordmark, page
// titles, child names); Noto Sans carries body/UI text for clinical
// clarity at small sizes.
const display = Bricolage_Grotesque({
  variable: "--font-display-face",
  subsets: ["latin"],
  weight: ["500", "600", "700"],
});

const body = Noto_Sans({
  variable: "--font-body-face",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

export const fontVariables = `${display.variable} ${body.variable}`;
