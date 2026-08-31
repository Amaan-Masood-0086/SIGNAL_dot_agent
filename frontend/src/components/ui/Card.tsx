import type { HTMLAttributes, ReactNode } from "react";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
}

export function Card({ children, className = "", ...props }: CardProps) {
  return (
    <div
      className={`rounded-xl border border-line bg-surface p-6 shadow-[0_1px_3px_rgba(21,40,37,0.06),0_8px_24px_-12px_rgba(21,40,37,0.12)] ${className}`}
      {...props}
    >
      {children}
    </div>
  );
}

export function CardTitle({ children }: { children: ReactNode }) {
  return (
    <h2 className="font-display text-xl font-semibold tracking-tight text-ink">
      {children}
    </h2>
  );
}

export function CardBody({ children }: { children: ReactNode }) {
  return <div className="mt-4">{children}</div>;
}
