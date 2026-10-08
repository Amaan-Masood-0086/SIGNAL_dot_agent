import Link from "next/link";
import { buttonClass } from "@/src/components/ui/Button";
export default function NotFound() {
  return <main className="mx-auto flex min-h-[65dvh] max-w-lg flex-col justify-center p-8"><p className="font-display text-xl font-bold text-pine">SIGNAL</p><h1 className="mt-8 font-display text-3xl font-semibold">This page is unavailable</h1><p className="mt-3 text-sm leading-relaxed text-ink-soft">The address may be incorrect, or this record may not be available to your account.</p><Link href="/dashboard" className={buttonClass("primary", "mt-6 self-start")}>Back to workspace</Link></main>;
}
