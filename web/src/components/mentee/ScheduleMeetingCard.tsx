"use client";

import { useState } from "react";
import { CalendarPlus, Check, X } from "lucide-react";
import { Card, CardHeader } from "@/components/ui/Card";
import { StatusPill } from "@/components/ui/Badge";
import { EmptyBlock } from "@/components/ui/States";
import { api, errorMessage } from "@/lib/api";
import { useScheduledMeetings } from "@/lib/hooks";
import { formatDateTime } from "@/lib/format";
import { mutate } from "swr";

export function ScheduleMeetingCard({ studentId }: { studentId: number }) {
  const { data: scheduled } = useScheduledMeetings(studentId);
  const [date, setDate] = useState("");
  const [time, setTime] = useState("10:00");
  const [mode, setMode] = useState("in_person");
  const [agenda, setAgenda] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!date) return;
    setSubmitting(true);
    setError(null);
    try {
      await api.scheduleMeeting({
        student_id: studentId,
        scheduled_for: new Date(`${date}T${time}`).toISOString(),
        mode,
        agenda: agenda.trim() || null,
      });
      setDate("");
      setAgenda("");
      await mutate(["scheduled-meetings", studentId]);
    } catch (err) {
      setError(errorMessage(err, "Could not schedule this meeting."));
    } finally {
      setSubmitting(false);
    }
  }

  async function respondToRequest(scheduleId: number, state: "scheduled" | "cancelled") {
    setBusyId(scheduleId);
    setError(null);
    try {
      await api.updateScheduleStatus(scheduleId, state);
      await mutate(["scheduled-meetings", studentId]);
    } catch (err) {
      setError(errorMessage(err, "Could not update this meeting request."));
    } finally {
      setBusyId(null);
    }
  }

  const upcoming = (scheduled ?? []).filter((m) => m.status === "scheduled" || m.status === "requested");

  return (
    <Card>
      <CardHeader title="Scheduled meetings" subtitle="Track completion against the required mentoring cadence" />
      <div className="mt-3 space-y-3 px-5 pb-5">
        {upcoming.length === 0 ? (
          <EmptyBlock message="No upcoming meeting scheduled yet." />
        ) : (
          <div className="space-y-2">
            {upcoming.map((m) => (
              <div key={m.id} className="rounded-lg border border-[var(--color-border)] px-3.5 py-2.5 text-sm">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div>
                    {formatDateTime(m.scheduled_for)} · {m.mode}
                    {m.agenda ? <p className="mt-0.5 text-xs text-[var(--color-muted)]">{m.agenda}</p> : null}
                  </div>
                  {m.status === "requested" ? (
                    <div className="flex items-center gap-2">
                      <StatusPill tone="warning">Requested by student</StatusPill>
                      <button
                        onClick={() => respondToRequest(m.id, "scheduled")}
                        disabled={busyId === m.id}
                        aria-label="Confirm meeting request"
                        className="flex h-7 w-7 items-center justify-center rounded-lg bg-[var(--color-status-low-bg)] text-[var(--color-status-low)] hover:opacity-80 disabled:opacity-50"
                      >
                        <Check size={14} />
                      </button>
                      <button
                        onClick={() => respondToRequest(m.id, "cancelled")}
                        disabled={busyId === m.id}
                        aria-label="Decline meeting request"
                        className="flex h-7 w-7 items-center justify-center rounded-lg bg-[var(--color-status-high-bg)] text-[var(--color-status-high)] hover:opacity-80 disabled:opacity-50"
                      >
                        <X size={14} />
                      </button>
                    </div>
                  ) : null}
                </div>
              </div>
            ))}
          </div>
        )}

        <form onSubmit={handleSubmit} className="grid grid-cols-2 gap-2 border-t border-[var(--color-border)] pt-3 sm:grid-cols-5">
          <input
            type="date"
            required
            value={date}
            onChange={(e) => setDate(e.target.value)}
            className="rounded-lg border border-[var(--color-border)] px-2.5 py-2 text-xs"
          />
          <input
            type="time"
            value={time}
            onChange={(e) => setTime(e.target.value)}
            className="rounded-lg border border-[var(--color-border)] px-2.5 py-2 text-xs"
          />
          <select value={mode} onChange={(e) => setMode(e.target.value)} className="rounded-lg border border-[var(--color-border)] px-2.5 py-2 text-xs">
            <option value="in_person">In person</option>
            <option value="online">Online</option>
            <option value="phone">Phone</option>
          </select>
          <input
            value={agenda}
            onChange={(e) => setAgenda(e.target.value)}
            placeholder="Agenda"
            className="col-span-2 rounded-lg border border-[var(--color-border)] px-2.5 py-2 text-xs sm:col-span-1"
          />
          <button
            type="submit"
            disabled={submitting}
            className="col-span-2 flex items-center justify-center gap-1.5 rounded-lg bg-[var(--color-brand-500)] px-3 py-2 text-xs font-semibold text-white hover:bg-[var(--color-brand-600)] disabled:opacity-60 sm:col-span-1"
          >
            <CalendarPlus size={13} /> Schedule
          </button>
        </form>
        {error ? <p className="text-xs text-[var(--color-status-high)]">{error}</p> : null}
      </div>
    </Card>
  );
}
