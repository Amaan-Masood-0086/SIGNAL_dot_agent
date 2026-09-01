import type { SVGProps } from "react";

// One inline stroke-icon set (no icon dependency, no CDN — CSP stays clean).
// 24px grid, 1.6 stroke, currentColor. Decorative by default: every icon is
// aria-hidden and its meaning is carried by adjacent text.
export type IconName =
  | "children"
  | "add-child"
  | "overview"
  | "key"
  | "staff"
  | "audit"
  | "usage"
  | "logout"
  | "menu"
  | "close"
  | "search"
  | "chevron-right"
  | "shield"
  | "alert"
  | "check";

const PATHS: Record<IconName, string> = {
  children:
    "M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8ZM4 20a8 8 0 0 1 16 0",
  "add-child": "M12 5v14M5 12h14",
  overview: "M4 13h7V4H4v9Zm9 7h7v-9h-7v9ZM4 20h7v-4H4v4ZM13 8h7V4h-7v4Z",
  key: "M15.5 8.5a4 4 0 1 1-3.9 5L8 17.5H5.5V15l1-1 1 1 1.5-1.5-1-1 2.6-2.6a4 4 0 0 1 4.9-1.4ZM16.5 7.5h.01",
  staff: "M9 11a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7ZM2.5 20a6.5 6.5 0 0 1 13 0M17 11.5a3 3 0 1 0 0-6M18 20h3.5a5.5 5.5 0 0 0-3.8-5.2",
  audit:
    "M6 3h8l4 4v14H6V3ZM14 3v4h4M9 12h6M9 16h6",
  usage: "M4 20V10M10 20V4M16 20v-7M22 20H2",
  logout: "M15 17l5-5-5-5M20 12H9M12 4H5v16h7",
  menu: "M4 7h16M4 12h16M4 17h16",
  close: "M6 6l12 12M18 6L6 18",
  search: "M11 18a7 7 0 1 0 0-14 7 7 0 0 0 0 14ZM20 20l-4-4",
  "chevron-right": "M9 5l7 7-7 7",
  shield: "M12 3l7 3v6c0 4.2-2.9 7.9-7 9-4.1-1.1-7-4.8-7-9V6l7-3Z",
  alert: "M12 8v5M12 16.5h.01M10.3 3.9 2.6 17a2 2 0 0 0 1.7 3h15.4a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z",
  check: "M4 12.5 9.5 18 20 7",
};

interface IconProps extends SVGProps<SVGSVGElement> {
  name: IconName;
}

export function Icon({ name, className = "h-5 w-5", ...props }: IconProps) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
      className={className}
      {...props}
    >
      <path d={PATHS[name]} />
    </svg>
  );
}
