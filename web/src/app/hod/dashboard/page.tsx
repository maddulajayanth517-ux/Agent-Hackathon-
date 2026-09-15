"use client";

import { Users, GraduationCap, ShieldAlert, Clock, Download } from "lucide-react";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, BarChart, Bar, XAxis, YAxis, CartesianGrid } from "recharts";
import { AppShell } from "@/components/AppShell";
import { StatCard } from "@/components/ui/StatCard";
import { HeroBanner } from "@/components/ui/HeroBanner";
import { Card, CardHeader } from "@/components/ui/Card";
import { LoadingBlock, ErrorBlock, EmptyBlock } from "@/components/ui/States";
import { useHodAnalytics, useComplianceReport } from "@/lib/hooks";
import { API_BASE_URL } from "@/lib/api";
import { riskMeta } from "@/lib/format";

function getToken(): string {
  return typeof window !== "undefined" ? window.localStorage.getItem("mentorflow_token") ?? "" : "";
}

function downloadEvidence(kind: "csv" | "pdf") {
  const token = getToken();
  fetch(`${API_BASE_URL}/reports/accreditation-evidence.${kind}`, {
    headers: { Authorization: `Bearer ${token}` },
  })
    .then((res) => res.blob())
    .then((blob) => {
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `agent45_accreditation_evidence.${kind}`;
      a.click();
      URL.revokeObjectURL(url);
    });
}

function HodDashboardBody() {
  const { data, error, isLoading } = useHodAnalytics();
  const { data: compliance } = useComplianceReport();

  if (isLoading) return <LoadingBlock label="Loading institution analytics…" />;
  if (error) return <ErrorBlock message={error.message} />;
  if (!data) return null;

  const statusData = Object.entries(data.student_status_distribution).map(([level, count]) => ({
    name: level,
    value: count,
    color: riskMeta(level).color,
  }));

  return (
    <div className="space-y-6">
      <HeroBanner
        title="Mentoring System Health"
        subtitle="Institution-wide compliance and outcomes."
        right={
          <div className="flex gap-2">
            <button
              onClick={() => downloadEvidence("csv")}
              className="flex items-center gap-1.5 rounded-lg border border-white/30 bg-white/10 px-3 py-2 text-xs font-semibold text-white transition-colors hover:bg-white/20"
            >
              <Download size={13} /> CSV evidence
            </button>
            <button
              onClick={() => downloadEvidence("pdf")}
              className="flex items-center gap-1.5 rounded-lg bg-white px-3 py-2 text-xs font-semibold text-[var(--color-brand-700)] transition-colors hover:bg-white/90"
            >
              <Download size={13} /> PDF summary
            </button>
          </div>
        }
      />

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard label="Total Mentors" value={data.totals.total_mentors} icon={Users} accent="purple" />
        <StatCard label="Total Mentees" value={data.totals.total_mentees} icon={GraduationCap} accent="blue" />
        <StatCard label="Open Escalations" value={data.totals.open_escalations} icon={ShieldAlert} accent="pink" />
        <StatCard label="Overdue Actions" value={data.totals.overdue_actions} icon={Clock} accent="green" />
      </div>

      {compliance ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <Card className="p-5 text-center">
            <p className="text-2xl font-semibold text-[var(--color-brand-600)]">
              {compliance.metrics.frequency_compliance_percent.toFixed(0)}%
            </p>
            <p className="mt-1 text-xs text-[var(--color-muted)]">Meeting compliance</p>
          </Card>
          <Card className="p-5 text-center">
            <p className="text-2xl font-semibold text-[var(--color-brand-600)]">
              {compliance.metrics.action_completion_rate_percent.toFixed(0)}%
            </p>
            <p className="mt-1 text-xs text-[var(--color-muted)]">Action closure rate</p>
          </Card>
          <Card className="p-5 text-center">
            <p className="text-2xl font-semibold text-[var(--color-brand-600)]">{compliance.metrics.total_meetings}</p>
            <p className="mt-1 text-xs text-[var(--color-muted)]">Total meetings logged</p>
          </Card>
        </div>
      ) : null}

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        <Card>
          <CardHeader title="Mentor workload distribution" />
          <div className="h-64 px-2 pb-4 pt-2">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.mentor_workload}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                <XAxis
                  dataKey="name"
                  tick={{ fontSize: 11, fill: "var(--color-muted)" }}
                  interval={0}
                  angle={-20}
                  textAnchor="end"
                  height={50}
                />
                <YAxis tick={{ fontSize: 11, fill: "var(--color-muted)" }} />
                <Tooltip />
                <Bar dataKey="active_students" fill="var(--color-brand-500)" radius={[6, 6, 0, 0]} name="Mentees" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card>
          <CardHeader title="Student status distribution" />
          <div className="h-64 px-2 pb-4 pt-2">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={statusData} dataKey="value" nameKey="name" innerRadius={55} outerRadius={85} paddingAngle={3}>
                  {statusData.map((entry) => (
                    <Cell key={entry.name} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      <Card className="p-5">
        <h3 className="text-sm font-semibold text-[var(--color-ink)]">Open escalations by destination</h3>
        <div className="mt-3 flex flex-wrap gap-3">
          {Object.entries(data.escalations_by_destination).length === 0 ? (
            <EmptyBlock message="No open escalations." />
          ) : (
            Object.entries(data.escalations_by_destination).map(([dest, count]) => (
              <div key={dest} className="rounded-xl border border-[var(--color-border)] px-4 py-2.5 text-sm">
                <span className="font-semibold text-[var(--color-ink)]">{count}</span>{" "}
                <span className="text-[var(--color-muted)]">{dest}</span>
              </div>
            ))
          )}
        </div>
      </Card>
    </div>
  );
}

export default function HodDashboardPage() {
  return (
    <AppShell allow={["hod", "admin"]}>
      <div className="mx-auto max-w-6xl px-4 py-6 sm:px-6 sm:py-8 lg:px-8">
        <HodDashboardBody />
      </div>
    </AppShell>
  );
}
