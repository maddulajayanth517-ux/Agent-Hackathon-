"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LogOut, X } from "lucide-react";
import clsx from "clsx";
import { useAuth } from "@/lib/auth";
import { NAV_BY_ROLE } from "@/lib/nav";
import { titleCase } from "@/lib/format";
import { Logo } from "./Logo";
import { ThemeToggle } from "./ui/ThemeToggle";

const ACCENTS = ["var(--color-accent-purple)", "var(--color-accent-green)", "var(--color-accent-blue)", "var(--color-accent-pink)"];

export function Sidebar({
  mobileOpen = false,
  onClose,
}: {
  mobileOpen?: boolean;
  onClose?: () => void;
}) {
  const { user, logout } = useAuth();
  const pathname = usePathname();
  if (!user) return null;
  const items = NAV_BY_ROLE[user.role] ?? [];

  return (
    <>
      {mobileOpen ? (
        <div className="fixed inset-0 z-30 bg-black/40 lg:hidden" onClick={onClose} aria-hidden="true" />
      ) : null}
      <aside
        className={clsx(
          "fixed inset-y-0 left-0 z-40 flex h-screen w-72 shrink-0 flex-col bg-gradient-to-b from-[var(--color-brand-950)] to-[var(--color-brand-800)] text-white transition-transform duration-200 ease-out lg:static lg:w-64 lg:translate-x-0",
          mobileOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div className="flex items-center justify-between gap-2.5 px-6 py-6">
          <div className="flex items-center gap-2.5">
            <Logo size={38} />
            <div>
              <p className="text-sm font-semibold leading-tight">Student Mentoring</p>
              <p className="text-[11px] text-white/50">Vignan&apos;s · Agent 45</p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close navigation menu"
            className="rounded-lg p-1.5 text-white/70 hover:bg-white/10 hover:text-white lg:hidden"
          >
            <X size={18} />
          </button>
        </div>

        <nav className="flex-1 space-y-1 overflow-y-auto px-3">
          {items.map((item, index) => {
            const active = pathname === item.href || pathname.startsWith(item.href + "/");
            const Icon = item.icon;
            const accent = ACCENTS[index % ACCENTS.length];
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={onClose}
                className={clsx(
                  "relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors duration-150",
                  active ? "bg-white/15 text-white" : "text-white/70 hover:bg-white/10 hover:text-white"
                )}
              >
                {active ? (
                  <span
                    className="absolute left-0 top-1/2 h-5 w-1 -translate-y-1/2 rounded-full"
                    style={{ backgroundColor: accent }}
                  />
                ) : null}
                <Icon size={17} style={active ? { color: accent } : undefined} aria-hidden="true" />
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="border-t border-white/10 px-4 py-4">
          <div className="mb-3 flex items-center justify-between gap-2 rounded-xl bg-white/5 px-3 py-2.5">
            <div className="min-w-0">
              <p className="text-xs font-semibold text-white">{titleCase(user.role)}</p>
              <p className="truncate text-[11px] text-white/50">{user.email}</p>
            </div>
            <ThemeToggle variant="dark" />
          </div>
          <button
            onClick={logout}
            className="flex w-full items-center gap-2 rounded-xl px-3 py-2 text-sm text-white/70 transition-colors hover:bg-white/10 hover:text-white"
          >
            <LogOut size={16} aria-hidden="true" />
            Sign out
          </button>
        </div>
      </aside>
    </>
  );
}
