"use client";

import { useMemo, useState } from "react";
import { Send } from "lucide-react";
import { AppShell } from "@/components/AppShell";
import { Card, CardHeader } from "@/components/ui/Card";
import { StatusPill } from "@/components/ui/Badge";
import { LoadingBlock, ErrorBlock, EmptyBlock } from "@/components/ui/States";
import { useStudentDashboard, useStudentMeetings, useStudentCorrections } from "@/lib/hooks";
import { useAuth } from "@/lib/auth";
import { api, errorMessage } from "@/lib/api";
import { formatDate, formatDateTime } from "@/lib/format";
import { mutate } from "swr";

function ActionRow({ action, isOwner, onChange }: { action: import("@/lib/types").ActionItem; isOwner: boolean; onChange: (status: string) => void }) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-lg border border-[var(--color-border)] px-3.5 py-2.5">
      <div className="min-w-0">
        <p className="text-sm font-medium text-[var(--color-ink)]">{action.title}</p>
        <p className="text-xs text-[var(--color-muted)]">Due {formatDate(action.due_date)}</p>
      </div>
      {isOwner ? (
        <select
          value={action.status}
          onChange={(e) => onChange(e.target.value)}
          aria-label={`Update status for ${action.title}`}
          className="shrink-0 rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-2 py-1 text-xs text-[var(--color-ink)]"
        >
          <option value="open">Open</option>
          <option value="in_progress">In progress</option>
          <option value="completed">Completed</option>
        </select>
      ) : (
        <StatusPill tone={action.status === "completed" ? "success" : action.status === "overdue" ? "danger" : "neutral"}>
          {action.status.replace("_", " ")}
        </StatusPill>
      )}
    </div>
  );
}

function CorrectionRequestForm({ studentId }: { studentId: number }) {
  const [fieldReference, setFieldReference] = useState("");
  const [description, setDescription] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!fieldReference.trim() || !description.trim()) return;
    setSubmitting(true);
    setError(null);
    setSuccess(false);
    try {
      await api.createCorrectionRequest({ field_reference: fieldReference.trim(), description: description.trim() });
      setFieldReference("");
      setDescription("");
      setSuccess(true);
      await mutate(["student-corrections", studentId]);
    } catch (err) {
      setError(errorMessage(err, "Could not send this correction request."));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-2">
      <input
        value={fieldReference}
        onChange={(e) => setFieldReference(e.target.value)}
        placeholder="What is incorrect? (e.g. Attendance percentage)"
        className="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-xs text-[var(--color-ink)]"
      />
      <textarea
        value={description}
        onChange={(e) => setDescription(e.target.value)}
        placeholder="Describe what you believe is wrong and what it should be."
        rows={3}
        className="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-xs text-[var(--color-ink)]"
      />
      <button
        type="submit"
        disabled={submitting}
        className="inline-flex items-center gap-1.5 rounded-lg bg-[var(--color-brand-500)] px-3.5 py-2 text-xs font-semibold text-white hover:bg-[var(--color-brand-600)] disabled:opacity-60"
      >
        <Send size={13} /> Send to my mentor
      </button>
      {error ? <p className="text-xs text-[var(--color-status-high)]">{error}</p> : null}
      {success ? <p className="text-xs text-[var(--color-status-low)]">Sent — your mentor has been notified.</p> : null}
    </form>
  );
}

function CorrectionStatusPill({ status }: { status: string }) {
  const tone = status === "resolved" ? "success" : status === "dismissed" ? "neutral" : "warning";
  return <StatusPill tone={tone}>{status}</StatusPill>;
}

function ActionsBody() {
  const { user } = useAuth();
  const { data: dashboard, isLoading, error } = useStudentDashboard();
  const studentId = dashboard?.student.id ?? null;
  const { data: meetings } = useStudentMeetings(studentId);
  const { data: corrections } = useStudentCorrections(studentId);

  const allActions = useMemo(() => {
    if (!meetings) return [];
    return meetings.flatMap((m) => m.action_items).sort((a, b) => (a.due_date ?? "").localeCompare(b.due_date ?? ""));
  }, [meetings]);

  async function updateStatus(actionId: number, status: string) {
    try {
      await api.updateAction(actionId, { status });
      await mutate(["student-meetings", studentId]);
    } catch {
      // Non-blocking: the select simply reverts on next refresh if this failed.
    }
  }

  if (isLoading) return <LoadingBlock label="Loading your action items…" />;
  if (error) return <ErrorBlock message={error.message} />;
  if (!dashboard) return null;

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-semibold text-[var(--color-ink)]">Action Items</h2>

      <Card>
        <CardHeader title="All action items" subtitle="From your mentoring meetings — update ones assigned to you" />
        <div className="mt-3 space-y-2 px-5 pb-5">
          {allActions.length === 0 ? (
            <EmptyBlock message="No action items recorded yet." />
          ) : (
            allActions.map((a) => (
              <ActionRow
                key={a.id}
                action={a}
                isOwner={a.owner_id === user?.id && a.status !== "completed" && a.status !== "cancelled"}
                onChange={(status) => updateStatus(a.id, status)}
              />
            ))
          )}
        </div>
      </Card>

      <Card className="p-5">
        <h3 className="text-sm font-semibold text-[var(--color-ink)]">Is this information correct?</h3>
        <p className="mt-1.5 text-xs text-[var(--color-muted)]">
          You have visibility into everything recorded about your mentoring. If something looks wrong, request a
          correction and your mentor will review it.
        </p>
        <div className="mt-3">{studentId ? <CorrectionRequestForm studentId={studentId} /> : null}</div>
        {corrections && corrections.length > 0 ? (
          <div className="mt-4 space-y-2 border-t border-[var(--color-border)] pt-3">
            {corrections.map((c) => (
              <div key={c.id} className="rounded-lg border border-[var(--color-border)] p-3">
                <div className="flex items-center justify-between gap-2">
                  <p className="text-xs font-semibold text-[var(--color-ink)]">{c.field_reference}</p>
                  <CorrectionStatusPill status={c.status} />
                </div>
                <p className="mt-1 text-xs text-[var(--color-muted)]">{c.description}</p>
                {c.resolution_notes ? (
                  <p className="mt-1.5 text-xs text-[var(--color-brand-600)]">Mentor: {c.resolution_notes}</p>
                ) : null}
                <p className="mt-1 text-[11px] text-[var(--color-muted)]">Sent {formatDateTime(c.created_at)}</p>
              </div>
            ))}
          </div>
        ) : null}
      </Card>
    </div>
  );
}

export default function StudentActionsPage() {
  return (
    <AppShell allow={["student"]}>
      <div className="mx-auto max-w-4xl px-4 py-6 sm:px-6 sm:py-8 lg:px-8">
        <ActionsBody />
      </div>
    </AppShell>
  );
}
