import clsx from "clsx";
import { riskMeta } from "@/lib/format";

export function SeverityBadge({ level, className }: { level: string; className?: string }) {
  const meta = riskMeta(level);
  return (
    <span
      className={clsx("inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold", className)}
      style={{ color: meta.color, backgroundColor: meta.bg }}
    >
      <span className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: meta.color }} />
      {meta.label}
    </span>
  );
}

export function StatusPill({
  tone,
  children,
}: {
  tone: "neutral" | "success" | "warning" | "danger" | "info";
  children: React.ReactNode;
}) {
  const toneMap: Record<string, string> = {
    neutral: "bg-[var(--color-brand-50)] text-[var(--color-brand-700)]",
    success: "bg-[var(--color-status-low-bg)] text-[var(--color-status-low)]",
    warning: "bg-[var(--color-status-medium-bg)] text-[var(--color-status-medium)]",
    danger: "bg-[var(--color-status-high-bg)] text-[var(--color-status-high)]",
    info: "bg-blue-50 text-blue-600",
  };
  return (
    <span className={clsx("inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold", toneMap[tone])}>
      {children}
    </span>
  );
}
