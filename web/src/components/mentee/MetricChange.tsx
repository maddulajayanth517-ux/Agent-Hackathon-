import { ArrowUp, ArrowDown, Minus } from "lucide-react";

export function MetricChange({
  label,
  from,
  to,
  unit,
  direction,
}: {
  label: string;
  from: number;
  to: number;
  unit: string;
  direction: "up" | "down" | "flat";
}) {
  const Icon = direction === "up" ? ArrowUp : direction === "down" ? ArrowDown : Minus;
  // Attendance/CGPA rising is good; backlog rising is bad — invert color logic for "Backlogs".
  const isBacklog = label.toLowerCase().includes("backlog");
  const positive = isBacklog ? direction === "down" : direction === "up";
  const color = direction === "flat" ? "var(--color-muted)" : positive ? "var(--color-status-low)" : "var(--color-status-high)";

  return (
    <div className="flex items-center justify-between rounded-xl border border-[var(--color-border)] px-3.5 py-2.5">
      <span className="text-xs font-medium text-[var(--color-muted)]">{label}</span>
      <span className="flex items-center gap-1.5 text-sm font-semibold" style={{ color }}>
        {from}
        {unit} <Icon size={13} /> {to}
        {unit}
      </span>
    </div>
  );
}
