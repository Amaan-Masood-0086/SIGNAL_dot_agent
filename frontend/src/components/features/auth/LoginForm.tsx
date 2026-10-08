"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState, type FormEvent } from "react";

import { Button } from "@/src/components/ui/Button";
import { Input } from "@/src/components/ui/Input";

function LoginFormInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const response = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      if (!response.ok) {
        // A 403 here is the CSRF origin check, not a bad password — telling
        // the operator to re-check working credentials sent them hunting in
        // the wrong place entirely (seen when serving through a dev tunnel).
        if (response.status === 403) {
          setError("Sign-in is blocked on this address. Ask your administrator to check the sign-in configuration.");
          return;
        }
        if (response.status === 429) {
          const wait = Number(response.headers.get("Retry-After") ?? 300);
          setError(
            `Too many sign-in attempts for this account. Wait about ${Math.ceil(
              wait / 60,
            )} minute(s) and try again.`,
          );
          return;
        }
        setError("Sign-in failed. Check your credentials and try again.");
        return;
      }
      // MUST #13: only allow-listed internal destinations.
      const next = searchParams.get("next");
      router.push(next && next.startsWith("/dashboard") ? next : "/dashboard");
      router.refresh();
    } catch {
      setError("Sign-in is unavailable right now. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div>
      <h2>Welcome back</h2>
      <p className="mt-2 text-sm leading-relaxed text-ink-soft">Sign in to your SIGNAL workspace.</p>
        <form onSubmit={onSubmit} className="flex flex-col gap-5">
          <Input
            id="login-email"
            label="Email"
            type="email"
            autoComplete="email"
            maxLength={320}
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <Input
            id="login-password"
            label="Password"
            type="password"
            autoComplete="current-password"
            maxLength={256}
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          {error && (
            <p role="alert" className="text-sm font-medium text-red">
              {error}
            </p>
          )}
          <Button type="submit" disabled={submitting} className="w-full">
            {submitting ? "Signing in…" : "Sign in"}
          </Button>
          <p className="text-center text-xs text-ink-soft">
            Use your assigned synthetic staff account. Your access is set by your administrator.
          </p>
        </form>
      <p className="mt-8 border-t border-line pt-5 text-xs leading-relaxed text-ink-soft">This workspace currently supports synthetic records only.</p>
    </div>
  );
}

// useSearchParams requires a Suspense boundary during static prerender.
export function LoginForm() {
  return (
    <Suspense fallback={null}>
      <LoginFormInner />
    </Suspense>
  );
}
