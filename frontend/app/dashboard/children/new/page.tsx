import Link from "next/link";

import { ChildIntakeForm } from "@/src/components/features/child-intake/ChildIntakeForm";
import { PageHeader } from "@/src/components/layout/PageHeader";

export const metadata = { title: "Register a child — SIGNAL" };

export default function NewChildPage() {
  return (
    <main className="mx-auto w-full max-w-2xl p-5 sm:p-8">
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
          lede="Record whether the date of birth is confirmed or estimated. An estimated age automatically downgrades the confidence of every age-dependent milestone check later — so record what you actually know, not a best guess presented as fact."
        />
      </div>
      <div className="mt-6">
        <ChildIntakeForm />
      </div>
    </main>
  );
}
