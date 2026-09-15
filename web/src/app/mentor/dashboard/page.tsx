"use client";

import Link from "next/link";
import { Users, CalendarCheck, ListChecks, BellRing, ArrowRight, Sparkles } from "lucide-react";
import { AppShell } from "@/components/AppShell";
import { StatCard } from "@/components/ui/StatCard";
import { HeroBanner } from "@/components/ui/HeroBanner";
import { Card, CardHeader } from "@/components/ui/Card";
import { SeverityBadge } from "@/components/ui/Badge";
import { LoadingBlock, ErrorBlock, EmptyBlock } from "@/components/ui/States";
import { useMentorDashboard } from "@/lib/hooks";
import { useAuth } from "@/lib/auth";
import { formatDateTime, greeting, nameFromEmail } from "@/lib/format";

function MentorDashboardBody() {
  const { user } = useAuth();
  const { data, error, isLoading } = useMentorDashboard();

  if (isLoading) return <LoadingBlock label="Preparing your dashboard…" />;
  if (error) return <ErrorBlock message={error.message} />;
  if (!data) return null;

  return (
    <div className="space-y-6">
      <HeroBanner
        title={`${greeting()}, ${nameFromEmail(user?.email)}`}
        subtitle={
          data.priority_queue.length > 0
            ? `${data.priority_queue.filter((s) => s.risk_level === "high" || s.risk_level === "critical").length} mentees need attention today.`
            : "Everything looks steady across your mentees today."
        }
      />

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard label="Mentees" value={data.counts.total_mentees} icon={Users} accent="purple" />
        <StatCard label="Meetings Today" value={data.counts.meetings_today} icon={CalendarCheck} accent="blue" />
        <StatCard label="Open Actions" value={data.counts.open_actions} icon={ListChecks} accent="green" />
        <StatCard label="New Alerts" value={data.counts.new_alerts} icon={BellRing} accent="pink" />
      </div>

      <Card>
        <CardHeader title="Today's Priority Queue" subtitle="Ranked by mentoring risk signal" />
        <div className="mt-3 divide-y divide-[var(--color-border)]">
          {data.priority_queue.length === 0 ? (
            <div className="px-5 pb-5">
              <EmptyBlock message="No mentees are flagged for attention right now." />
            </div>
          ) : (
            data.priority_queue.map((row) => (
              <Link
                key={row.student_id}
                href={`/mentor/mentees/${row.student_id}`}
                className="flex items-center justify-between gap-4 px-5 py-4 transition-colors hover:bg-[var(--color-brand-50)]"
              >
                <div className="min-w-0">
                  <p className="truncate text-sm font-semibold text-[var(--color-ink)]">{row.name}</p>
                  <p className="truncate text-xs text-[var(--color-muted)]">{row.top_issue}</p>
                </div>
                <div className="flex shrink-0 items-center gap-3">
                  <span className="hidden text-xs text-[var(--color-muted)] sm:inline">
                    {row.last_contact_days === null ? "No meeting yet" : `Last contact ${row.last_contact_days}d ago`}
                  </span>
                  <SeverityBadge level={row.risk_level} />
                  <ArrowRight size={15} className="text-[var(--color-muted)]" />
                </div>
              </Link>
            ))
          )}
        </div>
      </Card>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader title="Upcoming Meetings" />
          <div className="mt-3 divide-y divide-[var(--color-border)] pb-2">
            {data.upcoming_meetings.length === 0 ? (
              <div className="px-5 pb-5">
                <EmptyBlock message="No meetings scheduled yet." />
              </div>
            ) : (
              data.upcoming_meetings.map((m) => (
                <div key={m.id} className="flex items-center justify-between px-5 py-3">
                  <div>
                    <p className="text-sm font-medium text-[var(--color-ink)]">{m.student_name}</p>
                    <p className="text-xs text-[var(--color-muted)]">{formatDateTime(m.scheduled_for)} · {m.mode}</p>
                  </div>
                  <Link
                    href={`/mentor/mentees/${m.student_id}`}
                    className="flex items-center gap-1 rounded-lg bg-[var(--color-brand-50)] px-2.5 py-1.5 text-xs font-semibold text-[var(--color-brand-600)] hover:bg-[var(--color-brand-100)]"
                  >
                    <Sparkles size={13} /> Brief
                  </Link>
                </div>
              ))
            )}
          </div>
        </Card>

        <Card>
          <CardHeader title="Recent Alerts" />
          <div className="mt-3 divide-y divide-[var(--color-border)] pb-2">
            {data.recent_alerts.length === 0 ? (
              <div className="px-5 pb-5">
                <EmptyBlock message="No alerts right now." />
              </div>
            ) : (
              data.recent_alerts.map((alert) => (
                <div key={alert.id} className="px-5 py-3">
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-medium text-[var(--color-ink)]">{alert.title}</p>
                    <SeverityBadge level={alert.severity.toLowerCase()} />
                  </div>
                  <p className="mt-0.5 text-xs text-[var(--color-muted)]">{alert.body}</p>
                </div>
              ))
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}

export default function MentorDashboardPage() {
  return (
    <AppShell allow={["mentor", "admin"]}>
      <div className="mx-auto max-w-6xl px-4 py-6 sm:px-6 sm:py-8 lg:px-8">
        <MentorDashboardBody />
      </div>
    </AppShell>
  );
}
