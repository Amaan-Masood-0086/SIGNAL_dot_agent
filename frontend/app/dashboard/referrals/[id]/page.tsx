import Link from "next/link";
import { redirect } from "next/navigation";
import { requireStaff } from "@/src/lib/auth/rbac";
import { getSessionToken } from "@/src/lib/auth/session";
import { getReferral } from "@/src/lib/api/referrals";
import { getFlag } from "@/src/lib/api/flags";
import { ReferralForm } from "@/src/components/features/referrals/ReferralForm";
import { ReasoningTrail } from "@/src/components/features/reasoning/ReasoningTrail";
import { PageHeader } from "@/src/components/layout/PageHeader";
export const metadata = { title: "Referral follow-up | SIGNAL" };

export default async function ReferralPage({ params }: { params: Promise<{ id: string }> }) {
  const me = await requireStaff(); if (me.is_admin) redirect("/dashboard/admin");
  const token = (await getSessionToken()) ?? "";
  const referral = await getReferral(token, (await params).id);
  const flag = await getFlag(token, referral.flag_id);
  return <main className="mx-auto w-full max-w-3xl p-5 sm:p-8"><Link href="/dashboard/referrals" className="text-sm font-semibold text-pine">Back to referral queue</Link><div className="my-6"><PageHeader title="Referral follow-up" lede={referral.escalated ? "This referral is overdue. Review ownership, availability and the next action." : "Review progress and record the next follow-up."} /></div><section aria-label="Referral basis" className="mb-6 space-y-3"><p dir="auto" className="text-sm">{flag.explanation_text}</p><ReasoningTrail entries={flag.reasoning_trail} /><Link href={`/dashboard/sessions/${flag.session_id}`} className="inline-block text-sm font-semibold text-pine">Open original observation</Link></section><ReferralForm referral={referral} flagId={flag.id} /></main>;
}
