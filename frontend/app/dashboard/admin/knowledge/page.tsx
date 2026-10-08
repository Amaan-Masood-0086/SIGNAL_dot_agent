import { redirect } from "next/navigation";
import { z } from "zod";
import { requireStaff } from "@/src/lib/auth/rbac";
import { getSessionToken } from "@/src/lib/auth/session";
import { backendFetch } from "@/src/lib/api/client";
import { reviewCatalogSchema } from "@/src/lib/api/knowledge-review-schemas";
import { KnowledgeReviewPanel } from "@/src/components/features/admin/KnowledgeReviewPanel";
export const metadata = { title: "Knowledge base review | SIGNAL" };
export default async function KnowledgeReviewPage() {
  const me = await requireStaff(); if (!me.is_admin) redirect("/dashboard");
  const raw = await backendFetch("/api/v1/admin/knowledge-review", (await getSessionToken()) ?? "");
  const catalog = z.object({ data: reviewCatalogSchema }).parse(raw).data;
  return <KnowledgeReviewPanel initial={catalog} />;
}
