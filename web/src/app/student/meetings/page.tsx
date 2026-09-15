"use client";

import { useState } from "react";
import { CalendarPlus } from "lucide-react";
import { AppShell } from "@/components/AppShell";
import { Card, CardHeader } from "@/components/ui/Card";
import { StatusPill } from "@/components/ui/Badge";
import { LoadingBlock, ErrorBlock, EmptyBlock } from "@/components/ui/States";
import { useStudentDashboard, useStudentMeetings, useScheduledMeetings } from "@/lib/hooks";
import { api, errorMessage } from "@/lib/api";
import { formatDateTime } from "@/lib/format";
import { mutate } from "swr";

function RequestMeetingForm({ studentId }: { studentId: number }) {
  const [date, setDate] = useState("");
  const [time, setTime] = useState("10:00");
  const [mode, setMode] = useState("in_person");
  const [agenda, setAgenda] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!date) return;
    setSubmitting(true);
    setError(null);
    setSuccess(false);
    try {
      await api.requestMeeting({
        student_id: studentId,
        scheduled_for: new Date(`${date}T${time}`).toISOString(),
        mode,
        agenda: agenda.trim() || null,
      });
      setDate("");
      setAgenda("");
      setSuccess(true);
      await mutate(["scheduled-meetings", studentId]);
    } catch (err) {
      setError(errorMessage(err, "Could not send this meeting request."));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="grid grid-cols-2 gap-2 sm:grid-cols-5">
      <input
        type="date"
        required
        value={date}
        onChange={(e) => setDate(e.target.value)}
        aria-label="Requested date"
        className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-2.5 py-2 text-xs text-[var(--color-ink)]"
      />
      <input
        type="time"
        value={time}
        onChange={(e) => setTime(e.target.value)}
        aria-label="Requested time"
        className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-2.5 py-2 text-xs text-[var(--color-ink)]"
      />
      <select
        value={mode}
        onChange={(e) => setMode(e.target.value)}
        aria-label="Meeting mode"
        className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-2.5 py-2 text-xs text-[var(--color-ink)]"
      >
        <option value="in_person">In person</option>
        <option value="online">Online</option>
        <option value="phone">Phone</option>
      </select>
      <input
        value={agenda}
        onChange={(e) => setAgenda(e.target.value)}
        placeholder="What would you like to discuss?"
        className="col-span-2 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-2.5 py-2 text-xs text-[var(--color-ink)] sm:col-span-1"
      />
      <button
        type="submit"
        disabled={submitting}
        className="col-span-2 flex items-center justify-center gap-1.5 rounded-lg bg-[var(--color-brand-500)] px-3 py-2 text-xs font-semibold text-white hover:bg-[var(--color-brand-600)] disabled:opacity-60 sm:col-span-1"
      >
        <CalendarPlus size={13} /> Request
      </button>
      {error ? <p className="col-span-2 text-xs text-[var(--color-status-high)] sm:col-span-5">{error}</p> : null}
      {success ? (
        <p className="col-span-2 text-xs text-[var(--color-status-low)] sm:col-span-5">
          Request sent — your mentor will confirm it.
        </p>
      ) : null}
    </form>
  );
}

function MeetingsBody() {
  const { data: dashboard, isLoading: dashLoading, error: dashError } = useStudentDashboard();
  const studentId = dashboard?.student.id ?? null;
  const { data: meetings, isLoading: meetingsLoading, error: meetingsError } = useStudentMeetings(studentId);
  const { data: scheduled } = useScheduledMeetings(studentId);

  if (dashLoading || meetingsLoading) return <LoadingBlock label="Loading your meetings…" />;
  if (dashError) return <ErrorBlock message={dashError.message} />;
  if (meetingsError) return <ErrorBlock message={meetingsError.message} />;

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-semibold text-[var(--color-ink)]">My Meetings</h2>

      <Card>
        <CardHeader title="Upcoming" subtitle="Ask for a meeting if you don't want to wait for the next scheduled one" />
        <div className="mt-3 space-y-2 px-5 pb-5">
          {!scheduled || scheduled.length === 0 ? (
            <EmptyBlock message="No upcoming meetings scheduled." />
          ) : (
            scheduled.map((m) => (
              <div key={m.id} className="flex items-center justify-between gap-3 rounded-lg border border-[var(--color-border)] px-3.5 py-2.5 text-sm">
                <div>
                  {formatDateTime(m.scheduled_for)} · {m.mode}
                  {m.agenda ? <p className="mt-0.5 text-xs text-[var(--color-muted)]">{m.agenda}</p> : null}
                </div>
                {m.status === "requested" ? (
                  <StatusPill tone="warning">Awaiting mentor confirmation</StatusPill>
                ) : null}
              </div>
            ))
          )}
          {studentId ? (
            <div className="border-t border-[var(--color-border)] pt-3">
              <RequestMeetingForm studentId={studentId} />
            </div>
          ) : null}
        </div>
      </Card>

      <Card>
        <CardHeader title="Meeting history" />
        <div className="mt-3 space-y-2 px-5 pb-5">
          {!meetings || meetings.length === 0 ? (
            <EmptyBlock message="No meetings recorded yet." />
          ) : (
            meetings.map((m) => (
              <div key={m.id} className="rounded-lg border border-[var(--color-border)] p-3.5">
                <p className="text-sm font-medium text-[var(--color-ink)]">{formatDateTime(m.meeting_at)} · {m.mode}</p>
                {m.agenda ? <p className="mt-1 text-xs text-[var(--color-muted)]">Agenda: {m.agenda}</p> : null}
                {m.next_meeting_at ? (
                  <p className="mt-1 text-xs text-[var(--color-muted)]">Next: {formatDateTime(m.next_meeting_at)}</p>
                ) : null}
              </div>
            ))
          )}
        </div>
      </Card>
    </div>
  );
}

export default function StudentMeetingsPage() {
  return (
    <AppShell allow={["student"]}>
      <div className="mx-auto max-w-4xl px-4 py-6 sm:px-6 sm:py-8 lg:px-8">
        <MeetingsBody />
      </div>
    </AppShell>
  );
}
