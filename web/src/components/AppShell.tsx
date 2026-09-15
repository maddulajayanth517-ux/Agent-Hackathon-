"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Menu } from "lucide-react";
import { useAuth } from "@/lib/auth";
import { Sidebar } from "./Sidebar";
import { Logo } from "./Logo";

export function AppShell({
  children,
  allow,
}: {
  children: React.ReactNode;
  allow?: string[];
}) {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  useEffect(() => {
    if (loading) return;
    if (!user) {
      router.replace("/login");
      return;
    }
    if (allow && !allow.includes(user.role)) {
      router.replace("/login");
    }
  }, [loading, user, allow, router]);

  if (loading || !user || (allow && !allow.includes(user.role))) {
    return (
      <div className="flex h-screen items-center justify-center bg-[var(--color-canvas)]">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-[var(--color-brand-500)] border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="flex h-screen overflow-hidden bg-[var(--color-canvas)]">
      <Sidebar mobileOpen={mobileNavOpen} onClose={() => setMobileNavOpen(false)} />
      <div className="flex min-w-0 flex-1 flex-col">
        <div className="flex items-center gap-3 border-b border-[var(--color-border)] bg-[var(--color-surface)]/80 px-4 py-3 backdrop-blur lg:hidden">
          <button
            type="button"
            onClick={() => setMobileNavOpen(true)}
            aria-label="Open navigation menu"
            className="flex h-9 w-9 items-center justify-center rounded-lg border border-[var(--color-border)] text-[var(--color-ink)]"
          >
            <Menu size={18} />
          </button>
          <Logo size={30} />
          <span className="text-sm font-semibold text-[var(--color-ink)]">Student Mentoring</span>
        </div>
        <main className="flex-1 overflow-y-auto">
          <div className="animate-fade-up">{children}</div>
        </main>
      </div>
    </div>
  );
}
