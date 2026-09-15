import { AlertTriangle, Inbox } from "lucide-react";

export function LoadingBlock({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="flex items-center gap-3 rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] px-5 py-8 text-sm text-[var(--color-muted)]">
      <span className="h-4 w-4 animate-spin rounded-full border-2 border-[var(--color-brand-500)] border-t-transparent" />
      {label}
    </div>
  );
}

export function ErrorBlock({ message }: { message: string }) {
  return (
    <div className="flex items-start gap-3 rounded-2xl border border-[var(--color-status-high)]/30 bg-[var(--color-status-high-bg)] px-5 py-4 text-sm text-[var(--color-status-high)]">
      <AlertTriangle size={18} className="mt-0.5 shrink-0" />
      <div>
        <p className="font-semibold">Could not load this data</p>
        <p className="mt-0.5 text-xs opacity-90">{message}</p>
      </div>
    </div>
  );
}

export function EmptyBlock({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center gap-2 rounded-2xl border border-dashed border-[var(--color-border)] px-5 py-10 text-center text-sm text-[var(--color-muted)]">
      <Inbox size={20} />
      {message}
    </div>
  );
}
