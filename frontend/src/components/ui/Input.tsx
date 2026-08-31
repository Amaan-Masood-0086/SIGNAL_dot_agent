import type { InputHTMLAttributes } from "react";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
  hint?: string;
}

// Every input ships with a visible label (web-development.md MUST #11) and
// structured error/hint wiring for screen readers.
export function Input({ label, error, hint, id, className = "", ...props }: InputProps) {
  const describedBy =
    [error ? `${id}-error` : null, hint ? `${id}-hint` : null]
      .filter(Boolean)
      .join(" ") || undefined;

  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={id} className="text-sm font-medium text-ink-soft">
        {label}
      </label>
      <input
        id={id}
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy}
        className={`min-h-11 rounded-lg border bg-surface px-3 py-2 text-sm text-ink placeholder:text-ink-soft/60 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-pine ${
          error ? "border-red" : "border-line"
        } ${className}`}
        {...props}
      />
      {hint && !error && (
        <p id={`${id}-hint`} className="text-xs text-ink-soft">
          {hint}
        </p>
      )}
      {error && (
        <p id={`${id}-error`} role="alert" className="text-xs font-medium text-red">
          {error}
        </p>
      )}
    </div>
  );
}
