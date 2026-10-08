import { StaffPanel } from "@/src/components/features/admin/StaffPanel";
import { PageHeader } from "@/src/components/layout/PageHeader";
import { requireStaff } from "@/src/lib/auth/rbac";

export const metadata = { title: "Staff & roles · SIGNAL" };
export const dynamic = "force-dynamic";

export default async function AdminStaffPage() {
  const me = await requireStaff();

  return (
    <main className="mx-auto w-full max-w-6xl p-5 sm:p-8">
      <PageHeader
        eyebrow="Administration"
        title="Staff & roles"
        lede="Manage staff accounts, institution membership and access. Role changes take effect immediately and are recorded."
      />
      <div className="mt-6">
        <StaffPanel currentStaffId={me.staff_id} />
      </div>
    </main>
  );
}
