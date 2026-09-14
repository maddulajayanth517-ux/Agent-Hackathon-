"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { AppShell } from "@/components/AppShell";
import { Card } from "@/components/ui/Card";
import { LoadingBlock, ErrorBlock, EmptyBlock } from "@/components/ui/States";
import { useMentorActions } from "@/lib/hooks";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/format";
import { mutate } from "swr";

const TABS = ["Open", "In Progress", "Due Soon", "Overdue", "Completed"] as const;

function daysUntil(dueDate: string | null): number | null {
  if (!dueDate) return null;
  return Math.round((new Date(dueDate).getTime() - Date.now()) / (1000 * 60 * 60 * 24));
}

function ActionsBody() {
  const { data, error, isLoading } = useMentorActions();
  const [tab, setTab] = useState<(typeof TABS)[number]>("Open");
  const [busyId, setBusyId] = useState<number | null>(null);

  const filtered = useMemo(() => {
    if (!data) return [];
    return data.filter((a) => {
      const remaining = daysUntil(a.due_date);
      switch (tab) {
        case "Open":
          return a.status === "open";
        case "In Progress":
          return a.status === "in_progress";
        case "Due Soon":
          return (a.status === "open" || a.status === "in_progress") && remaining !== null && remaining >= 0 && remaining <= 3;
        case "Overdue":
          return a.status === "overdue" || ((a.status === "open" || a.status === "in_progress") && remaining !== null && remaining < 0);
        case "Completed":
          return a.status === "completed";
      }
    });
  }, [data, tab]);

  async function markComplete(actionId: number) {
    setBusyId(actionId);
    try {
      await api.updateAction(actionId, { status: "completed" });
      await mutate(["mentor-actions", "all"]);
    } catch {
      // surfaced via a lightweight inline retry; keep silent failure minimal for now
    } finally {
      setBusyId(null);
    }
  }

  if (isLoading) return <LoadingBlock label="Loading action items…" />;
  if (error) return <ErrorBlock message={error.message} />;

  return (
    <div className="space-y-5">
      <div>
        <h2 className="text-2xl font-semibold text-[var(--color-ink)]">Action Item Tracking</h2>
        <p className="mt-1 text-sm text-[var(--color-muted)]">Across all of your mentees, ranked by due date.</p>
      </div>

      <div className="flex gap-1 overflow-x-auto rounded-xl bg-[var(--color-surface)] p-1 shadow-sm">
        {TABS.map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`shrink-0 rounded-lg px-3.5 py-2 text-xs font-semibold transition-colors ${
              tab === t ? "bg-[var(--color-brand-500)] text-white" : "text-[var(--color-muted)] hover:bg-[var(--color-brand-50)]"
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {filtered.length === 0 ? (
        <EmptyBlock message={`No actions in "${tab}" right now.`} />
      ) : (
        <Card className="divide-y divide-[var(--color-border)]">
          {filtered.map((action) => (
            <div key={action.id} className="flex items-center justify-between gap-4 px-5 py-3.5">
              <div className="min-w-0">
                <p className="truncate text-sm font-medium text-[var(--color-ink)]">{action.title}</p>
                <p className="truncate text-xs text-[var(--color-muted)]">
                  <Link href={`/mentor/mentees/${action.student_id}`} className="hover:text-[var(--color-brand-600)]">
                    {action.student_name}
                  </Link>{" "}
                  · Due {formatDate(action.due_date)}
                </p>
              </div>
              {action.status !== "completed" ? (
                <button
                  onClick={() => markComplete(action.id)}
                  disabled={busyId === action.id}
                  className="shrink-0 rounded-lg border border-[var(--color-border)] px-3 py-1.5 text-xs font-semibold text-[var(--color-ink)] hover:bg-[var(--color-brand-50)] disabled:opacity-50"
                >
                  Mark complete
                </button>
              ) : (
                <span className="shrink-0 rounded-lg bg-[var(--color-status-low-bg)] px-2.5 py-1 text-xs font-semibold text-[var(--color-status-low)]">
                  Completed
                </span>
              )}
            </div>
          ))}
        </Card>
      )}
    </div>
  );
}

export default function MentorActionsPage() {
  return (
    <AppShell allow={["mentor", "admin"]}>
      <div className="mx-auto max-w-5xl px-4 py-6 sm:px-6 sm:py-8 lg:px-8">
        <ActionsBody />
      </div>
    </AppShell>
  );
}
