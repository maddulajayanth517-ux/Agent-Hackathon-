"use client";

import { AppShell } from "@/components/AppShell";
import { Card, CardHeader } from "@/components/ui/Card";
import { LoadingBlock, ErrorBlock } from "@/components/ui/States";
import { useComplianceReport, useMentorLoadReport } from "@/lib/hooks";

function ReportsBody() {
  const { data: compliance, error: complianceError, isLoading: complianceLoading } = useComplianceReport();
  const { data: load, isLoading: loadLoading } = useMentorLoadReport();

  if (complianceLoading) return <LoadingBlock label="Loading reports…" />;
  if (complianceError) return <ErrorBlock message={complianceError.message} />;
  if (!compliance) return null;

  const rows = [
    ["Active students", compliance.metrics.active_students],
    ["Active allocations", compliance.metrics.active_allocations],
    ["Meeting coverage", `${compliance.metrics.meeting_coverage_percent}%`],
    ["Cadence compliance", `${compliance.metrics.frequency_compliance_percent}%`],
    ["Cadence-overdue allocations", compliance.metrics.frequency_overdue_allocations],
    ["Open action items", compliance.metrics.open_actions],
    ["Overdue action items", compliance.metrics.overdue_actions],
    ["Action closure rate", `${compliance.metrics.action_completion_rate_percent}%`],
    ["Active flags", compliance.metrics.active_flags],
    ["Open escalations", compliance.metrics.open_escalations],
  ] as const;

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-semibold text-[var(--color-ink)]">Compliance & Insights</h2>

      <Card>
        <CardHeader title="Institutional metrics" subtitle="Live snapshot from mentoring records" />
        <div className="mt-3 grid grid-cols-1 gap-2 px-5 pb-5 sm:grid-cols-2">
          {rows.map(([label, value]) => (
            <div key={label} className="flex items-center justify-between rounded-lg border border-[var(--color-border)] px-3.5 py-2.5">
              <span className="text-xs text-[var(--color-muted)]">{label}</span>
              <span className="text-sm font-semibold text-[var(--color-ink)]">{value}</span>
            </div>
          ))}
        </div>
      </Card>

      <Card>
        <CardHeader title="Mentor workload register" />
        <div className="mt-3 overflow-x-auto px-5 pb-5">
          {loadLoading || !load ? (
            <LoadingBlock label="Loading mentor load…" />
          ) : (
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="text-xs uppercase tracking-wide text-[var(--color-muted)]">
                  <th className="pb-2">Mentor</th>
                  <th className="pb-2">Department</th>
                  <th className="pb-2">Mentees</th>
                  <th className="pb-2">Capacity</th>
                  <th className="pb-2">Utilization</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--color-border)]">
                {load.mentors.map((m) => (
                  <tr key={String(m.mentor_id)}>
                    <td className="py-2 font-medium text-[var(--color-ink)]">{String(m.full_name)}</td>
                    <td className="py-2 text-[var(--color-muted)]">{String(m.department)}</td>
                    <td className="py-2">{String(m.active_students)}</td>
                    <td className="py-2">{String(m.max_students)}</td>
                    <td className="py-2">{String(m.utilization_percent)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </Card>
    </div>
  );
}

export default function ReportsPage() {
  return (
    <AppShell allow={["admin", "hod", "counsellor"]}>
      <div className="mx-auto max-w-5xl px-4 py-6 sm:px-6 sm:py-8 lg:px-8">
        <ReportsBody />
      </div>
    </AppShell>
  );
}
