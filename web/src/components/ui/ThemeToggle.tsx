"use client";

import { Moon, Sun } from "lucide-react";
import clsx from "clsx";
import { applyTheme } from "@/lib/theme";

export function ThemeToggle({ variant = "surface" }: { variant?: "surface" | "dark" }) {
  function toggle() {
    const isDark = document.documentElement.getAttribute("data-theme") === "dark";
    applyTheme(isDark ? "light" : "dark");
  }

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label="Toggle color theme"
      title="Toggle color theme"
      className={clsx(
        "flex h-9 w-9 shrink-0 items-center justify-center rounded-full transition-colors",
        variant === "dark"
          ? "text-white/70 hover:bg-white/10 hover:text-white"
          : "border border-[var(--color-border)] text-[var(--color-muted)] hover:bg-[var(--color-brand-50)] hover:text-[var(--color-brand-600)]"
      )}
    >
      {/* Both icons are always in the DOM; CSS driven by the [data-theme]
          attribute (set before paint in the root layout) decides which one
          shows, so there is no client/server hydration mismatch. */}
      <Sun size={16} className="theme-icon-dark" />
      <Moon size={16} className="theme-icon-light" />
    </button>
  );
}
