import { ProvidersPanel } from "@/src/components/features/admin/ProvidersPanel";
import { PageHeader } from "@/src/components/layout/PageHeader";

export const metadata = { title: "Providers & keys · SIGNAL" };
export const dynamic = "force-dynamic";

export default function AdminProvidersPage() {
  return (
    <main className="mx-auto w-full max-w-5xl p-5 sm:p-8">
      <PageHeader
        eyebrow="Administration"
        title="Providers & keys"
        lede="Configure speech and reasoning services. Saved credentials are encrypted; only their last four characters remain visible."
      />
      <div className="mt-6">
        <ProvidersPanel />
      </div>
    </main>
  );
}
