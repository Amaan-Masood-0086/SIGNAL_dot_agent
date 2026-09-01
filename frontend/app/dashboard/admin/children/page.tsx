import { AdminChildrenPanel } from "@/src/components/features/admin/AdminChildrenPanel";
import { PageHeader } from "@/src/components/layout/PageHeader";

export const metadata = { title: "All children · SIGNAL" };
export const dynamic = "force-dynamic";

export default function AdminChildrenPage() {
  return (
    <main className="mx-auto w-full max-w-6xl p-5 sm:p-8">
      <PageHeader
        eyebrow="Administration"
        title="All children"
        lede="A read-only oversight roster spanning every institution. This is the only place children are visible across the tenant boundary — every caretaker-facing surface stays scoped to a single institution."
      />
      <div className="mt-6">
        <AdminChildrenPanel />
      </div>
    </main>
  );
}
