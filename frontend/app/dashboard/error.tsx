"use client";
import { Button } from "@/src/components/ui/Button";
export default function ErrorPage({ reset }: { reset: () => void }) {
  return <main className="mx-auto w-full max-w-3xl p-8"><div className="rounded-xl border border-line bg-surface p-8"><h1 className="font-display text-2xl font-semibold">This page could not be loaded</h1><p className="mt-3 text-sm text-ink-soft">Try again to reload the workspace. Your saved records have not been changed.</p><Button onClick={reset} className="mt-6">Try again</Button></div></main>;
}
