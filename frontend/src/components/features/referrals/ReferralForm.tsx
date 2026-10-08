"use client";
import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { Input } from "@/src/components/ui/Input";
import { Button } from "@/src/components/ui/Button";
import { Alert } from "@/src/components/ui/Alert";
import type { Referral } from "@/src/lib/api/referral-schemas";

export function ReferralForm({ flagId, referral }: { flagId: string; referral?: Referral }) {
  const router = useRouter();
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (pending) return;
    const data = new FormData(event.currentTarget);
    setPending(true); setError(null); setSaved(false);
    try {
      const response = await fetch(referral ? `/api/referrals/${referral.id}` : `/api/flags/${flagId}/referral`, {
        method: referral ? "PATCH" : "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ responsible_person: data.get("responsible_person"), review_date: data.get("review_date"), ...(referral ? { status: data.get("status") } : { caretaker_confirmed: data.get("confirmed") === "on" }) }),
      });
      const result = await response.json();
      if (!response.ok) { setError(result.detail ?? "Could not save referral."); return; }
      setSaved(true);
      router.push(`/dashboard/referrals/${result.referral.id}`);
      router.refresh();
    } catch { setError("Connection failed. Your entered details are still here; check the queue before retrying."); }
    finally { setPending(false); }
  }
  return <form onSubmit={submit} className="space-y-5">
    {error && <Alert tone="danger">{error}</Alert>}
    {saved && <p role="status" className="text-sm text-pine">Follow-up record saved.</p>}
    <Input id="referral-person" label="Responsible person" name="responsible_person" defaultValue={referral?.responsible_person ?? ""} required maxLength={200} disabled={pending} />
    <Input id="referral-date" label="Review date" type="date" name="review_date" defaultValue={referral?.review_date ?? ""} required disabled={pending} />
    {referral ? <div><label htmlFor="referral-status" className="block text-sm text-ink-soft">Follow-up status</label><select id="referral-status" name="status" defaultValue={referral.status} disabled={pending} className="mt-1 min-h-11 w-full rounded-lg border border-line bg-surface px-3 text-sm"><option value="referred">Referred</option><option value="pending_capacity">Waiting for capacity</option><option value="closed">Closed</option></select><p className="mt-2 text-xs text-ink-soft">Close only after your team has reviewed the referral outcome. Closing this record is not a clinical clearance.</p></div> : <label className="flex items-start gap-3 text-sm"><input type="checkbox" name="confirmed" required disabled={pending} className="mt-1 h-4 w-4" /><span>I confirm this referral and have checked who will own the follow-up.</span></label>}
    <Button type="submit" disabled={pending}>{pending ? "Saving…" : referral ? "Save follow-up" : "Confirm referral"}</Button>
  </form>;
}
