import { LoginForm } from "@/src/components/features/auth/LoginForm";
import { GrowthCurve } from "@/src/components/ui/GrowthCurve";

export const metadata = { title: "Sign in — SIGNAL" };

export default function LoginPage() {
  return (
    <main className="flex flex-1 flex-col items-center justify-center gap-8 p-6">
      <header className="flex flex-col items-center gap-3 text-center">
        <GrowthCurve className="h-12 w-48 text-pine" />
        <h1 className="font-display text-4xl font-bold tracking-tight text-ink">
          SIGNAL
        </h1>
        <p className="max-w-xs text-sm leading-relaxed text-ink-soft">
          Developmental screening for children in institutional care —
          every observation documented, every flag explained.
        </p>
      </header>
      <LoginForm />
    </main>
  );
}
