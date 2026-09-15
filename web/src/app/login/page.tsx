"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Users, Building2, HeartHandshake, Sparkles, Lock } from "lucide-react";
import { useAuth, homeForRole, ApiError } from "@/lib/auth";
import { Logo } from "@/components/Logo";
import { ThemeToggle } from "@/components/ui/ThemeToggle";

const TAGLINES = [
  { label: "Students Thrive", icon: Sparkles, accent: "var(--color-accent-purple)" },
  { label: "Mentors Enable", icon: Users, accent: "var(--color-accent-green)" },
  { label: "Institution Grows", icon: Building2, accent: "var(--color-accent-blue)" },
  { label: "Together We Succeed", icon: HeartHandshake, accent: "var(--color-accent-pink)" },
];

export default function LoginPage() {
  const { user, login, loading } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!loading && user) router.replace(homeForRole(user.role));
  }, [loading, user, router]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(email, password);
    } catch (err) {
      if (err instanceof ApiError) setError("Sign-in failed. Check your email and password.");
      else setError("Something went wrong. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen flex-col bg-[var(--color-canvas)]">
      <header className="flex flex-wrap items-center justify-between gap-4 border-b border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-4 sm:px-10">
        <div className="flex items-center gap-3">
          <Logo size={44} />
          <div>
            <p className="text-base font-semibold text-[var(--color-ink)]">Student Mentoring Agent</p>
            <p className="text-xs text-[var(--color-muted)]">Vignan&apos;s Foundation · Listen · Guide · Support · Empower</p>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-4">
          {TAGLINES.map((tag) => (
            <div key={tag.label} className="flex items-center gap-2">
              <span
                className="flex h-8 w-8 items-center justify-center rounded-full text-white"
                style={{ backgroundColor: tag.accent }}
                aria-label={tag.label}
              >
                <tag.icon size={15} aria-hidden="true" />
              </span>
              <span className="hidden text-xs font-medium text-[var(--color-muted)] md:inline">{tag.label}</span>
            </div>
          ))}
          <ThemeToggle />
        </div>
      </header>

      <div className="grid flex-1 grid-cols-1 lg:grid-cols-2">
        <div className="relative hidden overflow-hidden bg-gradient-to-br from-[var(--color-brand-900)] via-[var(--color-brand-700)] to-[var(--color-brand-500)] p-12 text-white lg:flex lg:flex-col lg:justify-between">
          <div className="absolute inset-0 opacity-20 [background-image:radial-gradient(circle_at_20%_20%,white,transparent_35%),radial-gradient(circle_at_80%_60%,white,transparent_30%)]" />
          <div className="relative animate-fade-up">
            <p className="text-sm font-medium text-white/70">Every Student · Every Step · A Brighter Tomorrow</p>
            <h1 className="mt-4 max-w-md text-4xl font-semibold leading-tight">
              More than Mentoring — A Journey Together
            </h1>
          </div>
          <blockquote className="relative animate-fade-up border-l-2 border-white/40 pl-4 text-white/80" style={{ animationDelay: "80ms" }}>
            &ldquo;Better Students, Brighter Futures.&rdquo;
          </blockquote>
        </div>

        <div className="flex items-center justify-center px-6 py-16">
          <div className="w-full max-w-sm animate-fade-up">
            <h2 className="text-2xl font-semibold text-[var(--color-ink)]">Welcome back</h2>
            <p className="mt-1 text-sm text-[var(--color-muted)]">Sign in to continue to your mentoring workspace.</p>

            <form onSubmit={handleSubmit} className="mt-8 space-y-4">
              <div>
                <label className="mb-1.5 block text-xs font-medium text-[var(--color-muted)]">
                  Institutional email
                </label>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-3.5 py-2.5 text-sm text-[var(--color-ink)] outline-none focus:border-[var(--color-brand-500)] focus:ring-2 focus:ring-[var(--color-brand-500)]/20"
                  placeholder="you@institution.edu"
                />
              </div>
              <div>
                <label className="mb-1.5 block text-xs font-medium text-[var(--color-muted)]">Password</label>
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-3.5 py-2.5 text-sm text-[var(--color-ink)] outline-none focus:border-[var(--color-brand-500)] focus:ring-2 focus:ring-[var(--color-brand-500)]/20"
                  placeholder="••••••••••••"
                />
              </div>

              {error ? (
                <p
                  role="alert"
                  className="rounded-lg bg-[var(--color-status-high-bg)] px-3 py-2 text-xs font-medium text-[var(--color-status-high)]"
                >
                  {error}
                </p>
              ) : null}

              <button
                type="submit"
                disabled={submitting}
                className="flex w-full items-center justify-center gap-2 rounded-xl bg-[var(--color-brand-500)] px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-all duration-150 hover:bg-[var(--color-brand-600)] hover:shadow-md active:scale-[0.98] disabled:opacity-60"
              >
                <Lock size={15} />
                {submitting ? "Signing in…" : "Sign In"}
              </button>
            </form>

            <p className="mt-6 text-center text-xs text-[var(--color-muted)]">
              Access adapts automatically to your role — Student · Mentor · HOD · Counsellor.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
