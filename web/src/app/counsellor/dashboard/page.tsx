"use client";

import { useState } from "react";
import Link from "next/link";
import { ShieldAlert, ArrowRight, CheckCircle2, MessageCircle } from "lucide-react";
import { AppShell } from "@/components/AppShell";
import { Card, CardHeader } from "@/components/ui/Card";
import { SeverityBadge, StatusPill } from "@/components/ui/Badge";
import { LoadingBlock, ErrorBlock, EmptyBlock } from "@/components/ui/States";
import { useMyEscalations } from "@/lib/hooks";
import { api } from "@/lib/api";
import { formatDateTime } from "@/lib/format";
import { mutate } from "swr";

const WORKFLOW = ["Escalation detected", "Routed to Counselling Cell", "Counsellor acknowledges", "Status updated"];

function CounsellorBody() {
  const { data, error, isLoading } = useMyEscalations();
  const [busyId, setBusyId] = useState<number | null>(null);
  const [notes, setNotes] = useState<Record<number, string>>({});

  async function updateStatus(id: number, status: string) {
    setBusyId(id);
    try {
      await api.updateEscalation(id, { status, resolution_notes: notes[id] || undefined });
      await mutate("my-escalations");
    } catch {
      // handled inline via disabled state; keep UX non-blocking
    } finally {
      setBusyId(null);
    }
  }

  if (isLoading) return <LoadingBlock label="Loading the counselling queue…" />;
  if (error) return <ErrorBlock message={error.message} />;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold text-[var(--color-ink)]">Counselling Integration</h2>
        <p className="mt-1 text-sm text-[var(--color-muted)]">
          Personal and emotional escalations routed from mentors, visible only to you and named institutional roles.
        </p>
      </div>

      <Card className="flex flex-wrap items-center gap-2 p-4">
        {WORKFLOW.map((step, i) => (
          <span key={step} className="flex items-center gap-2">
            <span className="rounded-full bg-[var(--color-brand-50)] px-3 py-1.5 text-xs font-semibold text-[var(--color-brand-600)]">
              {step}
            </span>
            {i < WORKFLOW.length - 1 ? <ArrowRight size={13} className="text-[var(--color-muted)]" /> : null}
          </span>
        ))}
      </Card>

      <Card>
        <CardHeader title="Escalations assigned to you" />
        <div className="mt-3 space-y-3 px-5 pb-5">
          {!data || data.length === 0 ? (
            <EmptyBlock message="No escalations currently routed to you." />
          ) : (
            data.map((esc) => (
              <div key={esc.id} className="rounded-xl border border-[var(--color-border)] p-4">
                <div className="flex items-center justify-between gap-3">
                  <div className="flex items-center gap-2">
                    <ShieldAlert size={15} className="text-[var(--color-accent-pink)]" />
                    <p className="text-sm font-medium text-[var(--color-ink)]">{esc.reason}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <SeverityBadge level={esc.severity} />
                    <StatusPill tone={esc.status === "resolved" || esc.status === "closed" ? "success" : "warning"}>
                      {esc.status}
                    </StatusPill>
                  </div>
                </div>
                <p className="mt-1 text-xs text-[var(--color-muted)]">Received {formatDateTime(esc.created_at)}</p>
                <p className="mt-1 text-xs text-[var(--color-muted)]">
                  <span className="font-semibold text-[var(--color-brand-600)]">Why routed here?</span>{" "}
                  {esc.routing_explanation}
                </p>
                <Link
                  href={`/messages/${esc.student_id}`}
                  className="mt-2 inline-flex items-center gap-1.5 text-xs font-semibold text-[var(--color-brand-600)] hover:text-[var(--color-brand-700)]"
                >
                  <MessageCircle size={13} /> Message this student
                </Link>

                {esc.status !== "resolved" && esc.status !== "closed" ? (
                  <div className="mt-3 flex flex-col gap-2 sm:flex-row">
                    <input
                      value={notes[esc.id] ?? ""}
                      onChange={(e) => setNotes((prev) => ({ ...prev, [esc.id]: e.target.value }))}
                      placeholder="Resolution notes (kept in this confidential queue only)"
                      className="flex-1 rounded-lg border border-[var(--color-border)] px-3 py-2 text-xs"
                    />
                    {esc.status === "open" ? (
                      <button
                        onClick={() => updateStatus(esc.id, "acknowledged")}
                        disabled={busyId === esc.id}
                        className="shrink-0 rounded-lg border border-[var(--color-border)] px-3 py-2 text-xs font-semibold hover:bg-[var(--color-brand-50)] disabled:opacity-50"
                      >
                        Acknowledge
                      </button>
                    ) : null}
                    <button
                      onClick={() => updateStatus(esc.id, "resolved")}
                      disabled={busyId === esc.id}
                      className="flex shrink-0 items-center gap-1.5 rounded-lg bg-[var(--color-brand-500)] px-3 py-2 text-xs font-semibold text-white hover:bg-[var(--color-brand-600)] disabled:opacity-50"
                    >
                      <CheckCircle2 size={13} /> Mark resolved
                    </button>
                  </div>
                ) : null}
              </div>
            ))
          )}
        </div>
      </Card>
    </div>
  );
}

export default function CounsellorDashboardPage() {
  return (
    <AppShell allow={["counsellor", "admin"]}>
      <div className="mx-auto max-w-4xl px-4 py-6 sm:px-6 sm:py-8 lg:px-8">
        <CounsellorBody />
      </div>
    </AppShell>
  );
}
