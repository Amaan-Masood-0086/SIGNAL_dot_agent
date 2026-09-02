import Link from "next/link";

import { PageHeader } from "@/src/components/layout/PageHeader";
import { Alert } from "@/src/components/ui/Alert";
import { Badge } from "@/src/components/ui/Badge";
import { Icon, type IconName } from "@/src/components/ui/Icon";
import { StatTile } from "@/src/components/ui/StatTile";
import {
  getAllUsage,
  getAuditChainStatus,
  listAllChildren,
  listAuditLog,
  listProviderStatuses,
  listStaff,
} from "@/src/lib/api/admin";
import { requireStaff } from "@/src/lib/auth/rbac";
import { getSessionToken } from "@/src/lib/auth/session";

export const metadata = { title: "Admin overview · SIGNAL" };
export const dynamic = "force-dynamic";

/** Every tile degrades on its own — one dead endpoint must not blank the page. */
async function settle<T>(promise: Promise<T>): Promise<T | null> {
  try {
    return await promise;
  } catch {
    return null;
  }
}

const QUICK_LINKS: { href: string; label: string; description: string; icon: IconName }[] = [
  {
    href: "/dashboard/admin/providers",
    label: "Providers & keys",
    description: "Store or rotate the speech and LLM credentials, then test the live connection.",
    icon: "key",
  },
  {
    href: "/dashboard/admin/staff",
    label: "Staff & roles",
    description: "Promote, demote, deactivate. Every change is written to the audit chain.",
    icon: "staff",
  },
  {
    href: "/dashboard/admin/audit",
    label: "Audit log",
    description: "The tamper-evident record of who did what, with a hash-chain integrity check.",
    icon: "audit",
  },
  {
    href: "/dashboard/admin/usage",
    label: "Usage & cost",
    description: "Paid-provider calls broken down by staff member and institution.",
    icon: "usage",
  },
];

export default async function AdminOverviewPage() {
  // The layout gate renders a refusal for non-admins, but App Router renders
  // layout and page in PARALLEL — a layout withholding {children} does not
  // stop this component executing. Without this check a caretaker's visit
  // still fired six admin API calls (all correctly 403, all swallowed by
  // settle()). No data leaked; the work was simply done for nobody. Checking
  // here is what makes the refusal structural rather than cosmetic.
  const me = await requireStaff();
  if (!me.is_admin) {
    return null;
  }

  const token = (await getSessionToken()) ?? "";

  const [providers, staff, children, audit, chain, usage] = await Promise.all([
    settle(listProviderStatuses(token)),
    settle(listStaff(token)),
    settle(listAllChildren(token)),
    settle(listAuditLog(token)),
    settle(getAuditChainStatus(token)),
    settle(getAllUsage(token)),
  ]);

  const configured = providers?.filter((provider) => provider.configured).length ?? 0;
  const providerCount = providers?.length ?? 0;
  const institutions = usage?.by_institution.length ?? 0;
  const cost = usage?.total.estimated_cost ?? 0;

  return (
    <main className="mx-auto w-full max-w-6xl p-5 sm:p-8">
      <PageHeader
        eyebrow="Administration"
        title="System overview"
        lede="System-level state across every institution. Caretaker-facing surfaces stay strictly institution-scoped — the cross-institution views live only under Administration."
      />

      <div className="mt-6 grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatTile
          label="Staff accounts"
          value={staff?.total ?? "—"}
          hint="Across all institutions"
          tone="pine"
        />
        <StatTile
          label="Children"
          value={children?.total ?? "—"}
          hint={institutions > 0 ? `In ${institutions} institution(s) with activity` : "System-wide"}
        />
        <StatTile
          label="Providers"
          value={providerCount ? `${configured}/${providerCount}` : "—"}
          hint={
            configured === providerCount && providerCount > 0
              ? "Both providers hold an active credential"
              : "An unconfigured provider falls back to synthetic behaviour"
          }
          tone={providerCount > 0 && configured < providerCount ? "amber" : "pine"}
        />
        <StatTile
          label="Audit entries"
          value={audit?.total ?? "—"}
          hint={
            chain
              ? chain.chain_intact
                ? `Hash chain intact · ${chain.entries_checked} verified`
                : `Chain broken at #${chain.first_broken_sequence}`
              : "Integrity check unavailable"
          }
          tone={chain && !chain.chain_intact ? "red" : "neutral"}
        />
      </div>

      {chain && !chain.chain_intact && (
        <div className="mt-4">
          <Alert tone="danger">
            The audit hash chain no longer verifies from sequence{" "}
            {chain.first_broken_sequence}. Treat every record after that point as
            unproven and investigate before relying on it.
          </Alert>
        </div>
      )}

      <div className="mt-8 grid gap-4 lg:grid-cols-2">
        <section className="rounded-xl border border-line bg-surface p-5">
          <div className="flex flex-wrap items-center gap-2">
            <h2 className="mr-auto font-display text-lg font-semibold text-ink">
              Provider status
            </h2>
            <Link
              href="/dashboard/admin/providers"
              className="text-xs font-semibold text-pine hover:underline"
            >
              Manage →
            </Link>
          </div>
          {providers === null ? (
            <p className="mt-3 text-sm text-ink-soft">Provider status is unavailable.</p>
          ) : (
            <ul className="mt-3 space-y-2">
              {providers.map((provider) => (
                <li
                  key={provider.provider}
                  className="flex flex-wrap items-center gap-2 rounded-lg border border-line p-3"
                >
                  <span className="mr-auto text-sm font-semibold text-ink">
                    {provider.provider === "stt" ? "Speech-to-text" : "LLM"}
                    <span className="ml-2 text-xs font-normal text-ink-soft">
                      {provider.backend}
                    </span>
                  </span>
                  {provider.configured ? (
                    <Badge tone={provider.source === "ui" ? "success" : "warning"}>
                      {provider.source === "ui" ? "Key stored in app" : "From environment"}
                    </Badge>
                  ) : (
                    <Badge tone="neutral">Not configured</Badge>
                  )}
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="rounded-xl border border-line bg-surface p-5">
          <div className="flex flex-wrap items-center gap-2">
            <h2 className="mr-auto font-display text-lg font-semibold text-ink">
              Paid-provider spend
            </h2>
            <Link
              href="/dashboard/admin/usage"
              className="text-xs font-semibold text-pine hover:underline"
            >
              Breakdown →
            </Link>
          </div>
          {usage === null ? (
            <p className="mt-3 text-sm text-ink-soft">Usage data is unavailable.</p>
          ) : (
            <>
              {/* Flat figures, not nested tiles — a card inside a card
                  reads as two levels of hierarchy where there is only one. */}
              <dl className="mt-3 flex flex-wrap gap-x-10 gap-y-4">
                <div>
                  <dt className="text-[11px] font-semibold tracking-[0.12em] text-ink-soft uppercase">
                    Calls
                  </dt>
                  <dd className="mt-1 font-display text-3xl leading-none font-bold tracking-tight text-ink">
                    {usage.total.calls}
                  </dd>
                </div>
                <div>
                  <dt className="text-[11px] font-semibold tracking-[0.12em] text-ink-soft uppercase">
                    Estimated cost
                  </dt>
                  <dd
                    className={`mt-1 font-display text-3xl leading-none font-bold tracking-tight ${
                      cost > 0 ? "text-amber" : "text-ink"
                    }`}
                  >
                    ${cost.toFixed(4)}
                  </dd>
                </div>
              </dl>
              <p className="mt-3 text-xs leading-relaxed text-ink-soft">
                Cost visibility is the reporting half of the cost-abuse control —
                rate limits cap the damage, these numbers make it visible.
              </p>
            </>
          )}
        </section>
      </div>

      <h2 className="mt-8 font-display text-lg font-semibold text-ink">Administration tools</h2>
      <ul className="mt-3 grid gap-3 sm:grid-cols-2">
        {QUICK_LINKS.map((link) => (
          <li key={link.href}>
            <Link
              href={link.href}
              className="group flex h-full items-start gap-3 rounded-xl border border-line bg-surface p-4 transition-colors hover:border-pine/50 hover:bg-moss/40 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-pine"
            >
              <span className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-moss text-pine">
                <Icon name={link.icon} className="h-4.5 w-4.5" />
              </span>
              <span className="min-w-0">
                <span className="block font-display text-base font-semibold text-ink group-hover:text-pine-deep">
                  {link.label}
                </span>
                <span className="mt-1 block text-xs leading-relaxed text-ink-soft">
                  {link.description}
                </span>
              </span>
              <Icon
                name="chevron-right"
                className="mt-1 h-4 w-4 shrink-0 text-ink-soft transition-transform group-hover:translate-x-0.5"
              />
            </Link>
          </li>
        ))}
      </ul>
    </main>
  );
}
