import Link from "next/link";
import { redirect } from "next/navigation";
import { requireStaff } from "@/src/lib/auth/rbac";

import { ChildIntakeForm } from "@/src/components/features/child-intake/ChildIntakeForm";
import { PageHeader } from "@/src/components/layout/PageHeader";

export const metadata = { title: "Register a child — SIGNAL" };

export default async function NewChildPage() {
  const me = await requireStaff();
  if (me.is_admin) redirect("/dashboard/admin/children");
  return (
    <main className="mx-auto w-full max-w-4xl p-5 sm:p-8">
      <Link
        href="/dashboard"
        className="inline-flex text-sm font-medium text-pine hover:underline"
      >
        ← All children
      </Link>
      <div className="mt-3">
        <PageHeader
          eyebrow="Intake"
          title="Register a child"
          lede="Start with what you know. If there is no documented date of birth, record an estimated age range."
        />
      </div>
      <div className="mt-6">
        <ChildIntakeForm />
      </div>
    </main>
  );
}
