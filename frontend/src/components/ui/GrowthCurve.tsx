// Signature motif: a pediatric growth-chart curve with plotted milestone
// dots. Decorative only — hidden from assistive tech.
export function GrowthCurve({ className = "" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 220 56"
      fill="none"
      aria-hidden="true"
      className={className}
    >
      {/* chart grid */}
      <path
        d="M0 14h220M0 28h220M0 42h220M28 0v56M76 0v56M124 0v56M172 0v56"
        stroke="currentColor"
        strokeOpacity="0.14"
        strokeWidth="1"
      />
      {/* milestone curve */}
      <path
        d="M4 50C40 46 62 38 92 28s70-16 124-20"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
      />
      {/* plotted milestones */}
      <circle cx="52" cy="42" r="3.5" fill="currentColor" />
      <circle cx="112" cy="25" r="3.5" fill="currentColor" />
      <circle cx="178" cy="11" r="3.5" fill="currentColor" />
    </svg>
  );
}
