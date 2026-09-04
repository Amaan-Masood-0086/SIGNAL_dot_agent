"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/src/components/ui/Button";

export function LogoutButton({ className = "" }: { className?: string } = {}) {
  const router = useRouter();
  const [pending, setPending] = useState(false);

  async function onLogout() {
    setPending(true);
    try {
      await fetch("/api/auth/logout", { method: "POST" });
      router.push("/login");
      router.refresh();
    } finally {
      setPending(false);
    }
  }

  return (
    <Button
      variant="secondary"
      onClick={onLogout}
      disabled={pending}
      aria-label="Sign out"
      className={className}
    >
      {pending ? "Signing out…" : "Sign out"}
    </Button>
  );
}
