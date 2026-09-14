"use client";

import { use, useState } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  Sparkles,
  ChevronDown,
  ChevronUp,
  CalendarClock,
  ListChecks,
  History as HistoryIcon,
  LayoutGrid,
  MessageCircle,
} from "lucide-react";
import { AppShell } from "@/components/AppShell";
import { Card, CardHeader } from "@/components/ui/Card";
import { SeverityBadge } from "@/components/ui/Badge";
import { LoadingBlock, ErrorBlock, EmptyBlock } from "@/components/ui/States";
import { MetricChange } from "@/components/mentee/MetricChange";
import { MeetingForm } from "@/components/mentee/MeetingForm";
import { ScheduleMeetingCard } from "@/components/mentee/ScheduleMeetingCard";
import { FlagsPanel } from "@/components/mentee/FlagsPanel";
import { CorrectionsPanel } from "@/components/mentee/CorrectionsPanel";
import { MessageThread } from "@/components/mentee/MessageThread";
import { useStudentBrief, useWhatChanged, useStudentMeetings } from "@/lib/hooks";
import { useAuth } from "@/lib/auth";
import { api, errorMessage } from "@/lib/api";
import { formatDate, formatDateTime, initials } from "@/lib/format";
import { mutate } from "swr";

type Tab = "overview" | "brief" | "meeting" | "history" | "messages";

function EvidenceList({ items }: { items: string[] }) {
  const [open, setOpen] = useState(false);
  if (items.length === 0) return null;
  return (
    <div className="rounded-xl border border-[var(--color-border)]">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between px-3.5 py-2.5 text-xs font-semibold text-[var(--color-brand-600)]"
      >
        Why? — {items.length} supporting record{items.length === 1 ? "" : "s"}
        {open ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
      </button>
      {open ? (
        <ul className="space-y-1 border-t border-[var(--color-border)] px-3.5 py-2.5 text-xs text-[var(--color-muted)]">
          {items.map((item, i) => (
            <li key={i}>· {item}</li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}

function MenteeDetailBody({ studentId }: { studentId: number }) {
  const { user } = useAuth();
  const [tab, setTab] = useState<Tab>("overview");
  const { data: brief, error: briefError, isLoading: briefLoading } = useStudentBrief(studentId);
  const { data: changed } = useWhatChanged(studentId);
  const { data: meetings } = useStudentMeetings(studentId);
  const [actionError, setActionError] = useState<string | null>(null);

  if (briefLoading) return <LoadingBlock label="Loading mentee profile…" />;
  if (briefError) return <ErrorBlock message={briefError.message} />;
  if (!brief) return null;

  async function refreshAll() {
    await Promise.all([
      mutate(["student-brief", studentId]),
      mutate(["what-changed", studentId]),
      mutate(["student-meetings", studentId]),
      mutate("mentor-dashboard"),
    ]);
  }

  async function updateActionStatus(actionId: number, status: string) {
    setActionError(null);
    try {
      await api.updateAction(actionId, { status });
      await refreshAll();
    } catch (err) {
      setActionError(errorMessage(err, "Could not update this action."));
    }
  }

  const tabs: Array<{ key: Tab; label: string; icon: typeof LayoutGrid }> = [
    { key: "overview", label: "Overview", icon: LayoutGrid },
    { key: "brief", label: "Pre-Meeting Brief", icon: Sparkles },
    { key: "meeting", label: "Record Meeting", icon: CalendarClock },
    { key: "history", label: "History & Actions", icon: HistoryIcon },
    { key: "messages", label: "Messages", icon: MessageCircle },
  ];

  return (
    <div className="space-y-6">
      <Link href="/mentor/mentees" className="flex items-center gap-1.5 text-xs font-semibold text-[var(--color-muted)] hover:text-[var(--color-ink)]">
        <ArrowLeft size={14} /> Back to mentees
      </Link>

      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <span className="flex h-14 w-14 items-center justify-center rounded-full bg-[var(--color-brand-100)] text-lg font-semibold text-[var(--color-brand-600)]">
            {initials(brief.student.name)}
          </span>
          <div>
            <h2 className="text-xl font-semibold text-[var(--color-ink)]">{brief.student.name}</h2>
            <p className="text-sm text-[var(--color-muted)]">
              {brief.student.register_number} · {brief.student.department} · Year {brief.student.year}
            </p>
          </div>
        </div>
        <SeverityBadge level={brief.risk.level} className="text-sm" />
      </div>

      <div className="flex gap-1 overflow-x-auto rounded-xl bg-[var(--color-surface)] p-1 shadow-sm">
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`flex flex-1 items-center justify-center gap-1.5 rounded-lg px-3 py-2 text-xs font-semibold transition-colors ${
              tab === t.key ? "bg-[var(--color-brand-500)] text-white" : "text-[var(--color-muted)] hover:bg-[var(--color-brand-50)]"
            }`}
          >
            <t.icon size={14} /> {t.label}
          </button>
        ))}
      </div>

      {tab === "overview" ? (
        <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
          <div className="space-y-5 lg:col-span-2">
            <Card className="p-5">
              <h3 className="text-sm font-semibold text-[var(--color-ink)]">Key insights</h3>
              <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-4">
                <div className="rounded-xl bg-[var(--color-brand-50)] p-3 text-center">
                  <p className="text-lg font-semibold text-[var(--color-brand-600)]">
                    {brief.institutional_context?.profile?.attendance_pct != null
                      ? `${brief.institutional_context.profile.attendance_pct}%`
                      : "—"}
                  </p>
                  <p className="text-[11px] text-[var(--color-muted)]">Attendance</p>
                </div>
                <div className="rounded-xl bg-[var(--color-brand-50)] p-3 text-center">
                  <p className="text-lg font-semibold text-[var(--color-brand-600)]">
                    {brief.institutional_context?.profile?.cgpa != null ? String(brief.institutional_context.profile.cgpa) : "—"}
                  </p>
                  <p className="text-[11px] text-[var(--color-muted)]">CGPA</p>
                </div>
                <div className="rounded-xl bg-[var(--color-brand-50)] p-3 text-center">
                  <p className="text-lg font-semibold text-[var(--color-brand-600)]">{brief.summary.open_actions}</p>
                  <p className="text-[11px] text-[var(--color-muted)]">Open actions</p>
                </div>
                <div className="rounded-xl bg-[var(--color-brand-50)] p-3 text-center">
                  <p className="text-lg font-semibold text-[var(--color-brand-600)]">{brief.summary.total_meetings}</p>
                  <p className="text-[11px] text-[var(--color-muted)]">Meetings</p>
                </div>
              </div>
            </Card>

            <ScheduleMeetingCard studentId={studentId} />

            <Card>
              <CardHeader title="What changed since the last meeting?" />
              <div className="mt-3 space-y-2 px-5 pb-5">
                {changed && changed.metric_changes.length > 0 ? (
                  changed.metric_changes.map((m) => (
                    <MetricChange key={m.label} label={m.label} from={m.from} to={m.to} unit={m.unit} direction={m.direction} />
                  ))
                ) : (
                  <p className="text-xs text-[var(--color-muted)]">
                    {changed?.has_baseline
                      ? "No institutional metric changes recorded since the last meeting."
                      : "No prior meeting yet — metric deltas will appear after the first meeting is recorded."}
                  </p>
                )}
                {changed && changed.new_signals.length > 0 ? (
                  <div className="pt-2">
                    <p className="text-xs font-semibold text-[var(--color-ink)]">New signals</p>
                    <ul className="mt-1 space-y-1 text-xs text-[var(--color-muted)]">
                      {changed.new_signals.map((s, i) => (
                        <li key={i}>· {s}</li>
                      ))}
                    </ul>
                  </div>
                ) : null}
                {changed && changed.actions_completed_since_last_meeting.length > 0 ? (
                  <div className="pt-2">
                    <p className="text-xs font-semibold text-[var(--color-status-low)]">Completed since last meeting</p>
                    <ul className="mt-1 space-y-1 text-xs text-[var(--color-muted)]">
                      {changed.actions_completed_since_last_meeting.map((s, i) => (
                        <li key={i}>✓ {s}</li>
                      ))}
                    </ul>
                  </div>
                ) : null}
              </div>
            </Card>
          </div>

          <div className="space-y-5">
            <Card className="p-5">
              <h3 className="text-sm font-semibold text-[var(--color-ink)]">Risk summary</h3>
              <p className="mt-2 text-xs text-[var(--color-muted)]">
                Score {brief.risk.score} ·{" "}
                {brief.recommendations[0] ?? "Continue regular mentoring review."}
              </p>
              <div className="mt-3">
                <EvidenceList items={brief.risk.evidence} />
              </div>
            </Card>
            <Card>
              <CardHeader title="Flags" subtitle="Risk signals that alert this student's mentor" />
              <div className="mt-3 px-5 pb-5">
                <FlagsPanel studentId={studentId} />
              </div>
            </Card>
          </div>
        </div>
      ) : null}

      {tab === "brief" ? (
        <Card>
          <div className="flex items-center justify-between">
            <CardHeader title="Pre-Meeting Brief" subtitle={`Last meeting: ${brief.latest_meeting ? formatDate(brief.latest_meeting.meeting_at) : "None recorded"}`} />
            <button
              onClick={() => setTab("meeting")}
              className="mr-5 mt-5 h-fit shrink-0 rounded-lg bg-[var(--color-brand-500)] px-3.5 py-2 text-xs font-semibold text-white hover:bg-[var(--color-brand-600)]"
            >
              Start meeting
            </button>
          </div>
          <div className="mt-4 space-y-4 px-5 pb-5">
            <section>
              <h4 className="text-xs font-semibold uppercase tracking-wide text-[var(--color-muted)]">What&apos;s changed?</h4>
              {changed && changed.metric_changes.length > 0 ? (
                <div className="mt-2 grid grid-cols-1 gap-2 sm:grid-cols-3">
                  {changed.metric_changes.map((m) => (
                    <MetricChange key={m.label} label={m.label} from={m.from} to={m.to} unit={m.unit} direction={m.direction} />
                  ))}
                </div>
              ) : (
                <p className="mt-1 text-sm text-[var(--color-ink)]">No metric changes since the last meeting.</p>
              )}
            </section>
            <section>
              <h4 className="text-xs font-semibold uppercase tracking-wide text-[var(--color-muted)]">Suggested discussion points</h4>
              <ul className="mt-1.5 space-y-1 text-sm text-[var(--color-ink)]">
                {brief.discussion_points.map((d, i) => (
                  <li key={i}>· {d}</li>
                ))}
              </ul>
            </section>
            <section>
              <h4 className="text-xs font-semibold uppercase tracking-wide text-[var(--color-muted)]">Pending actions</h4>
              {brief.pending_actions.length === 0 ? (
                <p className="mt-1 text-sm text-[var(--color-ink)]">No pending actions.</p>
              ) : (
                <ul className="mt-1.5 space-y-1 text-sm text-[var(--color-ink)]">
                  {brief.pending_actions.map((p, i) => (
                    <li key={i}>· {p}</li>
                  ))}
                </ul>
              )}
            </section>
            <section>
              <h4 className="text-xs font-semibold uppercase tracking-wide text-[var(--color-muted)]">Alerts / flags</h4>
              {brief.risk.alerts.length === 0 ? (
                <p className="mt-1 text-sm text-[var(--color-ink)]">No active alerts.</p>
              ) : (
                <ul className="mt-1.5 space-y-1 text-sm text-[var(--color-status-high)]">
                  {brief.risk.alerts.map((a, i) => (
                    <li key={i}>⚠ {a}</li>
                  ))}
                </ul>
              )}
              <div className="mt-2">
                <EvidenceList items={brief.risk.evidence} />
              </div>
            </section>
          </div>
        </Card>
      ) : null}

      {tab === "meeting" && user ? (
        <MeetingForm
          studentId={studentId}
          mentorUserId={user.id}
          studentUserId={brief.student.user_id}
          onCreated={refreshAll}
        />
      ) : null}

      {tab === "history" ? (
        <div className="space-y-5">
        <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
          <Card>
            <CardHeader title="Action items" />
            {actionError ? <p className="mt-2 px-5 text-xs text-[var(--color-status-high)]">{actionError}</p> : null}
            <div className="mt-3 space-y-2 px-5 pb-5">
              {brief.action_items.length === 0 ? (
                <EmptyBlock message="No action items recorded yet." />
              ) : (
                brief.action_items.map((action) => (
                  <div key={action.id} className="rounded-lg border border-[var(--color-border)] p-3">
                    <div className="flex items-center justify-between gap-2">
                      <p className="text-sm font-medium text-[var(--color-ink)]">{action.title}</p>
                      <select
                        value={action.status}
                        onChange={(e) => updateActionStatus(action.id, e.target.value)}
                        className="rounded-md border border-[var(--color-border)] px-2 py-1 text-xs"
                      >
                        <option value="open">Open</option>
                        <option value="in_progress">In progress</option>
                        <option value="completed">Completed</option>
                        <option value="overdue">Overdue</option>
                        <option value="cancelled">Cancelled</option>
                      </select>
                    </div>
                    <p className="mt-1 flex items-center gap-1.5 text-xs text-[var(--color-muted)]">
                      <ListChecks size={12} /> Due {formatDate(action.due_date)}
                    </p>
                  </div>
                ))
              )}
            </div>
          </Card>

          <Card>
            <CardHeader title="Meeting history" />
            <div className="mt-3 space-y-2 px-5 pb-5">
              {!meetings || meetings.length === 0 ? (
                <EmptyBlock message="No meetings recorded yet." />
              ) : (
                meetings.map((m) => (
                  <div key={m.id} className="rounded-lg border border-[var(--color-border)] p-3">
                    <p className="text-sm font-medium text-[var(--color-ink)]">{formatDateTime(m.meeting_at)} · {m.mode}</p>
                    <p className="mt-1 text-xs text-[var(--color-muted)] line-clamp-2">{m.notes}</p>
                  </div>
                ))
              )}
            </div>
          </Card>
        </div>
          <CorrectionsPanel studentId={studentId} />
        </div>
      ) : null}

      {tab === "messages" ? (
        <Card>
          <CardHeader title="Messages" subtitle="Visible to this student, their mentor, and any counsellor/HOD currently assigned to an open escalation" />
          <MessageThread studentId={studentId} />
        </Card>
      ) : null}
    </div>
  );
}

export default function MenteeDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const studentId = Number(id);
  return (
    <AppShell allow={["mentor", "admin"]}>
      <div className="mx-auto max-w-6xl px-4 py-6 sm:px-6 sm:py-8 lg:px-8">
        <MenteeDetailBody studentId={studentId} />
      </div>
    </AppShell>
  );
}
