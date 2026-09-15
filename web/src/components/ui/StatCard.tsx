import type { LucideIcon } from "lucide-react";
import { Card } from "./Card";

const ACCENTS = {
  purple: { bg: "bg-[var(--color-accent-purple)]/10", fg: "text-[var(--color-accent-purple)]", line: "var(--color-accent-purple)" },
  green: { bg: "bg-[var(--color-accent-green)]/10", fg: "text-[var(--color-accent-green)]", line: "var(--color-accent-green)" },
  blue: { bg: "bg-[var(--color-accent-blue)]/10", fg: "text-[var(--color-accent-blue)]", line: "var(--color-accent-blue)" },
  pink: { bg: "bg-[var(--color-accent-pink)]/10", fg: "text-[var(--color-accent-pink)]", line: "var(--color-accent-pink)" },
  brand: { bg: "bg-[var(--color-brand-500)]/10", fg: "text-[var(--color-brand-600)]", line: "var(--color-brand-500)" },
} as const;

export function StatCard({
  label,
  value,
  icon: Icon,
  accent = "brand",
  hint,
}: {
  label: string;
  value: string | number;
  icon: LucideIcon;
  accent?: keyof typeof ACCENTS;
  hint?: string;
}) {
  const palette = ACCENTS[accent];
  return (
    <Card className="card-hover relative overflow-hidden p-5">
      <span className="absolute inset-x-0 top-0 h-1" style={{ backgroundColor: palette.line }} />
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium uppercase tracking-wide text-[var(--color-muted)]">{label}</span>
        <span className={`flex h-9 w-9 items-center justify-center rounded-xl ${palette.bg}`}>
          <Icon className={palette.fg} size={18} />
        </span>
      </div>
      <div className="mt-3 text-2xl font-semibold text-[var(--color-ink)]">{value}</div>
      {hint ? <p className="mt-1 text-xs text-[var(--color-muted)]">{hint}</p> : null}
    </Card>
  );
}
