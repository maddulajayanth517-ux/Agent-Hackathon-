import type { RiskLevel } from "./types";

export function formatDate(value: string | null | undefined, opts?: Intl.DateTimeFormatOptions): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleDateString(undefined, opts ?? { month: "short", day: "numeric", year: "numeric" });
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export function relativeDays(value: string | null | undefined): string {
  if (!value) return "No date set";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "No date set";
  const diffMs = date.getTime() - Date.now();
  const days = Math.round(diffMs / (1000 * 60 * 60 * 24));
  if (days === 0) return "Today";
  if (days === 1) return "Tomorrow";
  if (days === -1) return "Yesterday";
  if (days > 1) return `In ${days} days`;
  return `${Math.abs(days)} days ago`;
}

export const RISK_META: Record<RiskLevel, { label: string; color: string; bg: string }> = {
  low: { label: "On Track", color: "var(--color-status-low)", bg: "var(--color-status-low-bg)" },
  medium: { label: "Medium", color: "var(--color-status-medium)", bg: "var(--color-status-medium-bg)" },
  high: { label: "High", color: "var(--color-status-high)", bg: "var(--color-status-high-bg)" },
  critical: { label: "Critical", color: "var(--color-status-critical)", bg: "var(--color-status-critical-bg)" },
};

export function riskMeta(level: string | undefined | null) {
  const key = (level ?? "low").toLowerCase() as RiskLevel;
  return RISK_META[key] ?? RISK_META.low;
}

export function titleCase(value: string): string {
  return value
    .replace(/_/g, " ")
    .replace(/\w\S*/g, (word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase());
}

export function nameFromEmail(email: string | null | undefined): string {
  if (!email) return "there";
  const local = email.split("@")[0] ?? "";
  return titleCase(local.replace(/[._]/g, " "));
}

export function greeting(): string {
  const hour = new Date().getHours();
  if (hour < 12) return "Good morning";
  if (hour < 17) return "Good afternoon";
  return "Good evening";
}

export function initials(name: string | null | undefined): string {
  if (!name) return "?";
  const parts = name.trim().split(/\s+/);
  return parts
    .slice(0, 2)
    .map((p) => p[0]?.toUpperCase() ?? "")
    .join("");
}
