"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState, type FormEvent } from "react";

import { Button } from "@/src/components/ui/Button";
import { Card, CardBody, CardTitle } from "@/src/components/ui/Card";
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
          const body = (await response.json().catch(() => ({}))) as {
            origin?: string;
            expected?: string;
          };
          setError(
            `Blocked before your credentials were checked: the browser is on ${
              body.origin ?? "an unknown origin"
            } but the server considers itself ${
              body.expected ?? "a different origin"
            }. Add the first to APP_ALLOWED_ORIGINS and restart.`,
          );
          return;
        }
        if (response.status === 429) {
          const wait = Number(response.headers.get("Retry-After") ?? 300);
          setError(
            `Too many sign-in attempts for this account. Your credentials are fine — wait about ${Math.ceil(
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
    <Card className="w-full max-w-md">
      <CardTitle>Sign in</CardTitle>
      <CardBody>
        <form onSubmit={onSubmit} className="flex flex-col gap-4" noValidate>
          <Input
            id="login-email"
            label="Email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <Input
            id="login-password"
            label="Password"
            type="password"
            autoComplete="current-password"
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
            Synthetic-data-only build — use any synthetic staff credentials.
          </p>
        </form>
      </CardBody>
    </Card>
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
