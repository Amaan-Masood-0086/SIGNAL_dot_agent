"use client";
import { useFormStatus } from "react-dom";
import { Button } from "@/src/components/ui/Button";
export function StartSessionButton({ mode }: { mode: "voice" | "text" }) {
  const { pending } = useFormStatus();
  return <Button type="submit" variant={mode === "text" ? "primary" : "secondary"} disabled={pending} aria-label={`Start a ${mode} observation session`}>{pending ? "Opening session…" : mode === "text" ? "Write an observation" : "Use voice"}</Button>;
}
