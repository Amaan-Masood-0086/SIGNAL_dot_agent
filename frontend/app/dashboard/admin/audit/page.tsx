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
        lede="An append-only record of who did what, chained by hash so that any edit to history is detectable. The console itself is under the same regime it administers — provider tests and role changes appear here too."
      />
      <div className="mt-6">
        <AuditPanel />
      </div>
    </main>
  );
}
