import type { TrailEntryRead } from "@/src/lib/api/schemas";

/**
 * The knowledge-base basis behind a screening result.
 *
 * This is the regulatory core of the product, not a detail view: the
 * non-device CDS carve-out (PROJECT_BRIEF §11) holds only while a
 * professional can independently review WHY a result was reached. So each
 * entry shows the knowledge-base row in full — the citation ref, what that
 * row actually says, and where it came from — rather than the bare ref.
 *
 * `refsOnly` is the degraded path: a live conclusion whose flag could not be
 * re-read still lists its refs, because showing an unexplained code beats
 * showing no basis at all.
 */
export function ReasoningTrail({
  entries,
  refsOnly,
}: {
  entries?: TrailEntryRead[];
  refsOnly?: string[];
}) {
  if (entries && entries.length > 0) {
    return (
      <ul className="space-y-2">
        {entries.map((entry) => (
          <li
            key={entry.citation_ref}
            className="rounded-lg border border-line bg-moss/50 p-3"
          >
            <div className="flex flex-wrap items-baseline gap-x-2 gap-y-1">
              <span className="rounded bg-pine px-1.5 py-0.5 font-mono text-[10px] font-bold tracking-wide text-white">
                {entry.citation_ref}
              </span>
              {entry.source && (
                <span className="text-[11px] text-ink-soft">{entry.source}</span>
              )}
            </div>
            <p className="mt-1.5 text-xs leading-relaxed text-ink">
              {entry.description ?? entry.basis ?? "Cited knowledge-base entry."}
            </p>
            {entry.kb_drifted && (
              // Showing the original wording is correct; hiding that the
              // reference has since changed would not be.
              <p className="mt-1.5 text-[11px] leading-relaxed text-amber">
                This knowledge-base entry has been revised since this result
                was recorded. The wording above is the basis the grade was
                actually made on.
              </p>
            )}
          </li>
        ))}
      </ul>
    );
  }

  if (refsOnly && refsOnly.length > 0) {
    return (
      <>
        <ul className="flex flex-wrap gap-1.5">
          {refsOnly.map((ref) => (
            <li
              key={ref}
              className="rounded bg-pine px-1.5 py-0.5 font-mono text-[10px] font-bold tracking-wide text-white"
            >
              {ref}
            </li>
          ))}
        </ul>
        <p className="mt-2 text-[11px] text-ink-soft">
          The full text of these entries could not be loaded just now. They are
          recorded with the result and appear in the screening history.
        </p>
      </>
    );
  }

  return null;
}
