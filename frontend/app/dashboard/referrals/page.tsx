import Link from "next/link";
import { redirect } from "next/navigation";
import { requireStaff } from "@/src/lib/auth/rbac";
import { getSessionToken } from "@/src/lib/auth/session";
import { listReferrals } from "@/src/lib/api/referrals";
import { referralStatus } from "@/src/lib/api/referral-schemas";
import { PageHeader } from "@/src/components/layout/PageHeader";
import { Badge } from "@/src/components/ui/Badge";

export const metadata = { title: "Referrals & follow-up | SIGNAL" };

export default async function ReferralsPage({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const me = await requireStaff(); if (me.is_admin) redirect("/dashboard/admin");
  const search = await searchParams;
  const page = Math.max(1, Math.min(100000, Number(search.page) || 1));
  const query = new URLSearchParams({ page: String(Math.floor(page)), page_size: "20" });
  const status = referralStatus.safeParse(search.status);
  if (status.success) query.set("status", status.data);
  if (search.overdue === "true") query.set("overdue", "true");
  const result = await listReferrals((await getSessionToken()) ?? "", query);
  const pageLink = (number: number) => { const next = new URLSearchParams(query); next.set("page", String(number)); return `/dashboard/referrals?${next}`; };
  return <main className="mx-auto w-full max-w-5xl p-5 sm:p-8">
    <PageHeader title="Referrals & follow-up" lede="Keep a named person and a review date attached to every referral. This queue records follow-up; it does not contact a clinician automatically." />
    <nav aria-label="Referral filters" className="my-6 flex flex-wrap gap-4 text-sm font-semibold text-pine"><Link href="/dashboard/referrals">All</Link><Link href="/dashboard/referrals?status=referred">Referred</Link><Link href="/dashboard/referrals?status=pending_capacity">Waiting for capacity</Link><Link href="/dashboard/referrals?overdue=true">Overdue</Link><Link href="/dashboard/referrals?status=closed">Closed</Link></nav>
    <p className="mb-3 text-sm text-ink-soft">{result.total} matching referrals</p>
    {result.items.length === 0 ? <p className="rounded-xl border border-line bg-surface p-6">No referrals in this view. Open a saved screening result to create one.</p> : <ul className="divide-y divide-line rounded-xl border border-line bg-surface">{result.items.map(item => <li key={item.id} className="p-5"><div className="flex flex-wrap items-center gap-3"><Link href={`/dashboard/referrals/${item.id}`} className="font-semibold text-pine">{item.responsible_person ?? "Responsible person not recorded"}</Link><Badge tone={item.escalated ? "danger" : "neutral"}>{item.escalated ? "Overdue" : item.status.replaceAll("_", " ")}</Badge><span className="text-sm text-ink-soft sm:ml-auto">Review: {item.review_date ?? "Not scheduled"}</span></div><p className="mt-2 break-all text-xs text-ink-soft">Referral {item.id}</p></li>)}</ul>}
    <nav aria-label="Referral pages" className="mt-5 flex gap-5 text-sm font-semibold text-pine">{page > 1 && <Link href={pageLink(page - 1)}>Previous</Link>}{page * result.page_size < result.total && <Link href={pageLink(page + 1)}>Next</Link>}</nav>
  </main>;
}
