import { HTMLAttributes } from "react";
import clsx from "clsx";

export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={clsx(
        "rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-[0_1px_2px_rgba(30,27,58,0.04),0_8px_24px_-16px_rgba(30,27,58,0.25)]",
        className
      )}
      {...props}
    />
  );
}

export function CardHeader({
  title,
  subtitle,
  action,
}: {
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="flex items-start justify-between gap-3 px-5 pt-5">
      <div>
        <h3 className="text-sm font-semibold text-[var(--color-ink)]">{title}</h3>
        {subtitle ? <p className="mt-0.5 text-xs text-[var(--color-muted)]">{subtitle}</p> : null}
      </div>
      {action}
    </div>
  );
}
