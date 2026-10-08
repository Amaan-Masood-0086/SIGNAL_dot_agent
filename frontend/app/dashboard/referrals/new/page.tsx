import Link from "next/link";
import { notFound, redirect } from "next/navigation";
import { z } from "zod";
import { requireStaff } from "@/src/lib/auth/rbac";
import { getSessionToken } from "@/src/lib/auth/session";
import { getFlag } from "@/src/lib/api/flags";
import { listReferrals } from "@/src/lib/api/referrals";
import { ReferralForm } from "@/src/components/features/referrals/ReferralForm";
import { ReasoningTrail } from "@/src/components/features/reasoning/ReasoningTrail";
import { PageHeader } from "@/src/components/layout/PageHeader";
export const metadata = { title: "Confirm a referral | SIGNAL" };

export default async function NewReferralPage({ searchParams }: { searchParams: Promise<{ flag?: string }> }) {
  const me = await requireStaff(); if (me.is_admin) redirect("/dashboard/admin");
  const parsed = z.uuid().safeParse((await searchParams).flag); if (!parsed.success) notFound();
  const token = (await getSessionToken()) ?? "";
  const flag = await getFlag(token, parsed.data);
  const [referred, waiting] = await Promise.all(["referred", "pending_capacity"].map(status => listReferrals(token, new URLSearchParams({ flag_id: flag.id, status, page_size: "1" }))));
  const existing = referred.items[0] ?? waiting.items[0];
  if (existing) redirect(`/dashboard/referrals/${existing.id}`);
  return <main className="mx-auto w-full max-w-3xl p-5 sm:p-8"><Link href={`/dashboard/sessions/${flag.session_id}`} className="text-sm font-semibold text-pine">Back to saved result</Link><div className="my-6"><PageHeader title="Confirm a referral" lede="Review the saved evidence, name the person responsible and agree a review date. No message is sent automatically." /></div><section aria-label="Referral basis" className="mb-6 space-y-3"><p dir="auto" className="text-sm">{flag.explanation_text}</p><ReasoningTrail entries={flag.reasoning_trail} /></section><ReferralForm flagId={flag.id} /></main>;
}
