import { UsagePanel } from "@/src/components/features/admin/UsagePanel";
import { PageHeader } from "@/src/components/layout/PageHeader";

export const metadata = { title: "Usage & cost · SIGNAL" };
export const dynamic = "force-dynamic";

export default function AdminUsagePage() {
  return (
    <main className="mx-auto w-full max-w-6xl p-5 sm:p-8">
      <PageHeader
        eyebrow="Administration"
        title="Usage & cost"
        lede="Paid-provider consumption broken down by staff member and institution, so an unusual pattern is visible long before it becomes an invoice."
      />
      <div className="mt-6">
        <UsagePanel />
      </div>
    </main>
  );
}
