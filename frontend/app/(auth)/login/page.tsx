import { LoginForm } from "@/src/components/features/auth/LoginForm";
import { GrowthCurve } from "@/src/components/ui/GrowthCurve";
import { Icon } from "@/src/components/ui/Icon";
export const metadata = { title: "Sign in | SIGNAL" };
export const dynamic = "force-dynamic";
export default function LoginPage() {
  return <main id="main-content" className="login-layout">
    <section className="login-story" aria-label="About SIGNAL">
      <div className="flex items-center gap-3"><span className="brand-mark"><GrowthCurve className="h-5 w-7" /></span><span className="brand-name">SIGNAL</span></div>
      <div className="login-story-copy"><h1>A clearer picture.<br />A better next step.</h1><p>Turn everyday observations into a shared record of each child’s development. Help the next person see what you see.</p><div className="mt-10 hidden items-center gap-3 text-sm font-medium text-pine-deep md:flex"><Icon name="children" /><span>Made for the people who care for children.</span></div></div>
      <p className="login-story-footer text-xs text-ink-soft">Observe with care. Follow up with confidence.</p>
    </section>
    <section className="login-form-side" aria-label="Staff sign in"><LoginForm /></section>
  </main>;
}
