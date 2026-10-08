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
        lede="Review child records across institutions, manage assignments and keep each roster up to date."
      />
      <div className="mt-6">
        <AdminChildrenPanel />
      </div>
    </main>
  );
}
