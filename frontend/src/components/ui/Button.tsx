import type { ButtonHTMLAttributes } from "react";

type Variant = "primary" | "secondary" | "ghost";

const variantClasses: Record<Variant, string> = {
  primary:
    "bg-pine text-white hover:bg-pine-deep focus-visible:outline-pine cursor-pointer",
  secondary:
    "border border-line bg-surface text-ink hover:border-pine/50 hover:bg-moss focus-visible:outline-pine cursor-pointer",
  ghost:
    "text-ink-soft hover:bg-moss hover:text-ink focus-visible:outline-pine cursor-pointer",
};

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
}

// Accessible by default: type is explicit (never an accidental submit),
// focus ring is always visible, and callers must supply a visible label or
// aria-label (web-development.md MUST #11).
export function Button({
  variant = "primary",
  type = "button",
  className = "",
  ...props
}: ButtonProps) {
  return (
    <button
      type={type}
      className={`inline-flex min-h-11 items-center justify-center gap-2 rounded-lg px-4 py-2 text-sm font-semibold transition-colors duration-150 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 disabled:cursor-not-allowed disabled:opacity-50 ${variantClasses[variant]} ${className}`}
      {...props}
    />
  );
}
