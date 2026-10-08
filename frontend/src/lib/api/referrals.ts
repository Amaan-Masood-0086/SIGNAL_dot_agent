import { backendFetch } from "./client";
import { referralEnvelope, referralPageEnvelope } from "./referral-schemas";
export async function listReferrals(token: string, query: URLSearchParams) {
  return referralPageEnvelope.parse(await backendFetch(`/api/v1/referrals?${query}`, token)).data;
}
export async function getReferral(token: string, id: string) {
  return referralEnvelope.parse(await backendFetch(`/api/v1/referrals/${id}`, token)).data;
}
