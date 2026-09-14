"use client";

import { useState } from "react";
import Link from "next/link";
import { CheckCircle2, Send } from "lucide-react";
import { AppShell } from "@/components/AppShell";
import { Card, CardHeader } from "@/components/ui/Card";
import { SeverityBadge, StatusPill } from "@/components/ui/Badge";
import { LoadingBlock, ErrorBlock, EmptyBlock } from "@/components/ui/States";
import { useMyAlerts, useMyEscalations, useStudentDirectory } from "@/lib/hooks";
import { api, errorMessage } from "@/lib/api";
import { formatDateTime } from "@/lib/format";
import { mutate } from "swr";

function AlertsSection() {
  const { data, error, isLoading } = useMyAlerts();
  if (isLoading) return <LoadingBlock label="Loading alerts…" />;
  if (error) return <ErrorBlock message={error.message} />;
  if (!data || data.length === 0) return <EmptyBlock message="No alerts right now." />;

  async function markRead(id: number) {
    await api.markAlertRead(id);
    await mutate(["my-alerts", false]);
  }

  return (
    <div className="divide-y divide-[var(--color-border)]">
      {data.map((alert) => (
        <div key={alert.id} className="flex items-start justify-between gap-4 px-5 py-3.5">
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <p className="text-sm font-medium text-[var(--color-ink)]">{alert.title}</p>
              <SeverityBadge level={alert.severity.toLowerCase()} />
            </div>
            <p className="mt-0.5 text-xs text-[var(--color-muted)]">{alert.body}</p>
            <p className="mt-1 text-[11px] text-[var(--color-muted)]">
              {formatDateTime(alert.created_at)} ·{" "}
              <Link href={`/mentor/mentees/${alert.student_id}`} className="hover:text-[var(--color-brand-600)]">
                View student
              </Link>
            </p>
          </div>
          {!alert.read_at ? (
            <button
              onClick={() => markRead(alert.id)}
              className="flex shrink-0 items-center gap-1 rounded-lg border border-[var(--color-border)] px-2.5 py-1.5 text-xs font-semibold hover:bg-[var(--color-brand-50)]"
            >
              <CheckCircle2 size={13} /> Mark read
            </button>
          ) : (
            <span className="shrink-0 text-[11px] text-[var(--color-muted)]">Read</span>
          )}
        </div>
      ))}
    </div>
  );
}

function EscalationsSection() {
  const { data, error, isLoading } = useMyEscalations();
  const { data: students } = useStudentDirectory();
  const [studentId, setStudentId] = useState<number | "">("");
  const [severity, setSeverity] = useState("medium");
  const [reason, setReason] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!studentId || !reason.trim()) return;
    setSubmitting(true);
    setFormError(null);
    setSuccess(false);
    try {
      await api.createEscalation({ student_id: studentId, severity, reason: reason.trim() });
      setReason("");
      setSuccess(true);
      await mutate("my-escalations");
    } catch (err) {
      setFormError(errorMessage(err, "Could not create escalation."));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-4">
      <form onSubmit={handleSubmit} className="grid grid-cols-1 gap-3 sm:grid-cols-[2fr_1fr_1fr_auto]">
        <select
          value={studentId}
          onChange={(e) => setStudentId(e.target.value ? Number(e.target.value) : "")}
          className="rounded-lg border border-[var(--color-border)] px-3 py-2 text-sm"
        >
          <option value="">Select student…</option>
          {students?.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name} · {s.register_number}
            </option>
          ))}
        </select>
        <select value={severity} onChange={(e) => setSeverity(e.target.value)} className="rounded-lg border border-[var(--color-border)] px-3 py-2 text-sm">
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
          <option value="critical">Critical</option>
        </select>
        <input
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          placeholder="Reason (academic, financial, personal…)"
          className="rounded-lg border border-[var(--color-border)] px-3 py-2 text-sm"
        />
        <button
          type="submit"
          disabled={submitting}
          className="flex items-center justify-center gap-1.5 rounded-lg bg-[var(--color-brand-500)] px-3.5 py-2 text-xs font-semibold text-white hover:bg-[var(--color-brand-600)] disabled:opacity-60"
        >
          <Send size={13} /> Escalate
        </button>
      </form>
      {formError ? <p className="text-xs text-[var(--color-status-high)]">{formError}</p> : null}
      {success ? <p className="text-xs text-[var(--color-status-low)]">Escalation routed successfully.</p> : null}

      {isLoading ? (
        <LoadingBlock label="Loading escalations…" />
      ) : error ? (
        <ErrorBlock message={error.message} />
      ) : !data || data.length === 0 ? (
        <EmptyBlock message="No escalations raised yet." />
      ) : (
        <div className="divide-y divide-[var(--color-border)] rounded-xl border border-[var(--color-border)]">
          {data.map((esc) => (
            <div key={esc.id} className="px-4 py-3">
              <div className="flex items-center justify-between gap-4">
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium text-[var(--color-ink)]">{esc.reason}</p>
                  <p className="text-xs text-[var(--color-muted)]">
                    Routed to {esc.destination} · {esc.priority} priority
                  </p>
                </div>
                <div className="flex shrink-0 items-center gap-2">
                  <SeverityBadge level={esc.severity} />
                  <StatusPill tone={esc.status === "resolved" || esc.status === "closed" ? "success" : "info"}>
                    {esc.status}
                  </StatusPill>
                </div>
              </div>
              <p className="mt-1.5 text-[11px] text-[var(--color-muted)]">
                <span className="font-semibold text-[var(--color-brand-600)]">Why?</span> {esc.routing_explanation}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function MentorAlertsPage() {
  return (
    <AppShell allow={["mentor", "admin"]}>
      <div className="mx-auto max-w-5xl space-y-6 px-4 py-6 sm:px-6 sm:py-8 lg:px-8">
        <h2 className="text-2xl font-semibold text-[var(--color-ink)]">Alerts & Escalations</h2>
        <Card>
          <CardHeader title="Alerts" subtitle="Between-meeting signals on your mentees" />
          <div className="mt-3">
            <AlertsSection />
          </div>
        </Card>
        <Card>
          <CardHeader title="Escalation routing" subtitle="Academic → HOD · Personal/emotional → Counselling Cell · Financial → Scholarship/Fee" />
          <div className="mt-4 px-5 pb-5">
            <EscalationsSection />
          </div>
        </Card>
      </div>
    </AppShell>
  );
}
