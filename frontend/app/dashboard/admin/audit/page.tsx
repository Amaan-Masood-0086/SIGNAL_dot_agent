import { AuditPanel } from "@/src/components/features/admin/AuditPanel";
import { PageHeader } from "@/src/components/layout/PageHeader";

export const metadata = { title: "Audit log · SIGNAL" };
export const dynamic = "force-dynamic";

export default function AdminAuditPage() {
  return (
    <main className="mx-auto w-full max-w-6xl p-5 sm:p-8">
      <PageHeader
        eyebrow="Administration"
        title="Audit log"
        lede="Review recorded actions across the system and verify the integrity of the audit history."
      />
      <div className="mt-6">
        <AuditPanel />
      </div>
    </main>
  );
}
