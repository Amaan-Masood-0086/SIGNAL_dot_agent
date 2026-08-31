// FEAT-01 skeleton placeholder; FEAT-02 added the authenticated entry
// point. Real feature routes live under /dashboard per the
// web-development.md build order — no features before their ticket.
import Link from "next/link";

import { Button } from "@/src/components/ui/Button";
import { GrowthCurve } from "@/src/components/ui/GrowthCurve";

export default function Home() {
  return (
    <main className="flex flex-1 items-center justify-center p-8">
      <div className="max-w-md text-center">
        <GrowthCurve className="mx-auto h-8 w-28 text-pine" />
        <h1 className="mt-3 font-display text-3xl font-bold tracking-tight text-pine-deep">
          SIGNAL
        </h1>
        <p className="mt-3 text-sm leading-relaxed text-ink-soft">
          Early language-development screening for children in institutional
          care.
        </p>
        <Link href="/dashboard" className="mt-6 inline-block">
          <Button aria-label="Open dashboard">Open dashboard</Button>
        </Link>
        <p className="mt-6 text-xs font-semibold tracking-[0.14em] text-ink-soft/70 uppercase">
          Synthetic data only
        </p>
      </div>
    </main>
  );
}
