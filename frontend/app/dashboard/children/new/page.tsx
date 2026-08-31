import Link from "next/link";

import { ChildIntakeForm } from "@/src/components/features/child-intake/ChildIntakeForm";

export const metadata = { title: "Register a child — SIGNAL" };

export default function NewChildPage() {
  return (
    <main className="mx-auto w-full max-w-2xl p-6 sm:p-8">
      <Link
        href="/dashboard"
        className="text-sm font-medium text-pine hover:underline"
      >
        ← All children
      </Link>
      <div className="mt-4">
        <ChildIntakeForm />
      </div>
    </main>
  );
}
