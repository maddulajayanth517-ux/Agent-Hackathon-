"use client";

import { CalendarClock, ListChecks, CheckCircle2, TrendingUp } from "lucide-react";
import { AppShell } from "@/components/AppShell";
import { StatCard } from "@/components/ui/StatCard";
import { HeroBanner } from "@/components/ui/HeroBanner";
import { Card, CardHeader } from "@/components/ui/Card";
import { SeverityBadge } from "@/components/ui/Badge";
import { LoadingBlock, ErrorBlock, EmptyBlock } from "@/components/ui/States";
import { useStudentDashboard } from "@/lib/hooks";
import { useAuth } from "@/lib/auth";
import { formatDateTime, formatDate, greeting, nameFromEmail } from "@/lib/format";

function StudentDashboardBody() {
  const { user } = useAuth();
  const { data, error, isLoading } = useStudentDashboard();

  if (isLoading) return <LoadingBlock label="Loading your dashboard…" />;
  if (error) return <ErrorBlock message={error.message} />;
  if (!data) return null;

  return (
    <div className="space-y-6">
      <HeroBanner
        title={`${greeting()}, ${data.student.name?.split(" ")[0] ?? nameFromEmail(user?.email)}`}
        subtitle="Here's where things stand."
        tone="warm"
        right={<SeverityBadge level={data.risk_level} />}
      />

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard label="Pending Actions" value={data.counts.pending_actions} icon={ListChecks} accent="purple" />
        <StatCard label="Completed" value={data.counts.completed_actions} icon={CheckCircle2} accent="green" />
        <StatCard
          label="Attendance"
          value={data.profile_snapshot.attendance_pct != null ? `${data.profile_snapshot.attendance_pct}%` : "—"}
          icon={TrendingUp}
          accent="blue"
        />
        <StatCard
          label="Current CGPA"
          value={data.profile_snapshot.cgpa != null ? String(data.profile_snapshot.cgpa) : "—"}
          icon={TrendingUp}
          accent="pink"
        />
      </div>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        <Card>
          <CardHeader title="Next mentoring meeting" />
          <div className="px-5 pb-5 pt-3">
            {data.next_meeting ? (
              <div className="flex items-center gap-3 rounded-xl bg-[var(--color-brand-50)] p-3.5">
                <CalendarClock size={18} className="text-[var(--color-brand-600)]" />
                <div>
                  <p className="text-sm font-semibold text-[var(--color-ink)]">
                    {formatDateTime(data.next_meeting.scheduled_for)}
                  </p>
                  <p className="text-xs text-[var(--color-muted)]">
                    {data.next_meeting.mode} {data.next_meeting.agenda ? `· ${data.next_meeting.agenda}` : ""}
                  </p>
                </div>
              </div>
            ) : (
              <EmptyBlock message="No meeting scheduled yet. Your mentor will confirm one soon." />
            )}
            {data.mentor ? (
              <p className="mt-3 text-xs text-[var(--color-muted)]">
                Mentor: <span className="font-medium text-[var(--color-ink)]">{data.mentor.name}</span>
              </p>
            ) : null}
          </div>
        </Card>

        <Card>
          <CardHeader title="My progress" />
          <div className="mt-3 space-y-2 px-5 pb-5">
            {data.open_actions.length === 0 ? (
              <EmptyBlock message="No open action items — nice work!" />
            ) : (
              data.open_actions.map((a) => (
                <div key={a.id} className="flex items-center justify-between rounded-lg border border-[var(--color-border)] px-3 py-2.5">
                  <p className="text-sm text-[var(--color-ink)]">{a.title}</p>
                  <span className="text-xs text-[var(--color-muted)]">{formatDate(a.due_date)}</span>
                </div>
              ))
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}

export default function StudentDashboardPage() {
  return (
    <AppShell allow={["student"]}>
      <div className="mx-auto max-w-5xl px-4 py-6 sm:px-6 sm:py-8 lg:px-8">
        <StudentDashboardBody />
      </div>
    </AppShell>
  );
}
