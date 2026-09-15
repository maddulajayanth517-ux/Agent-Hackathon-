"use client";

import { useState } from "react";
import { History } from "lucide-react";
import { AppShell } from "@/components/AppShell";
import { HeroBanner } from "@/components/ui/HeroBanner";
import { Card } from "@/components/ui/Card";
import { LoadingBlock, ErrorBlock, EmptyBlock } from "@/components/ui/States";
import { useAuditEvents } from "@/lib/hooks";
import { formatDateTime } from "@/lib/format";

const RESOURCE_TYPES = ["meeting", "action_item", "allocation", "escalation", "correction_request", "scheduled_meeting"];

function actionLabel(action: string): string {
  return action
    .toLowerCase()
    .split("_")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

function AuditBody() {
  const [resourceType, setResourceType] = useState<string | undefined>(undefined);
  const { data, error, isLoading } = useAuditEvents(resourceType);

  return (
    <div className="space-y-6">
      <HeroBanner
        title="Audit Trail"
        subtitle="Who did what, to which mentoring record, and when — for accreditation and trust."
      />

      <div className="flex flex-wrap items-center gap-2">
        <button
          onClick={() => setResourceType(undefined)}
          className={`rounded-lg px-3 py-1.5 text-xs font-semibold ${
            !resourceType ? "bg-[var(--color-brand-500)] text-white" : "border border-[var(--color-border)] text-[var(--color-muted)] hover:bg-[var(--color-brand-50)]"
          }`}
        >
          All records
        </button>
        {RESOURCE_TYPES.map((type) => (
          <button
            key={type}
            onClick={() => setResourceType(type)}
            className={`rounded-lg px-3 py-1.5 text-xs font-semibold ${
              resourceType === type ? "bg-[var(--color-brand-500)] text-white" : "border border-[var(--color-border)] text-[var(--color-muted)] hover:bg-[var(--color-brand-50)]"
            }`}
          >
            {type.replace("_", " ")}
          </button>
        ))}
      </div>

      <Card>
        <div className="px-5 pt-5">
          {isLoading ? (
            <LoadingBlock label="Loading audit trail…" />
          ) : error ? (
            <ErrorBlock message={error.message} />
          ) : !data || data.length === 0 ? (
            <EmptyBlock message="No audit events recorded yet." />
          ) : null}
        </div>
        {data && data.length > 0 ? (
          <div className="divide-y divide-[var(--color-border)]">
            {data.map((event) => (
              <div key={event.id} className="flex items-start gap-3 px-5 py-3.5">
                <History size={15} className="mt-0.5 shrink-0 text-[var(--color-brand-500)]" aria-hidden="true" />
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <p className="text-sm font-medium text-[var(--color-ink)]">
                      {event.actor_name} · {actionLabel(event.action)}
                    </p>
                    <p className="text-[11px] text-[var(--color-muted)]">{formatDateTime(event.created_at)}</p>
                  </div>
                  <p className="mt-0.5 text-xs text-[var(--color-muted)]">
                    {event.resource_type}
                    {event.resource_id != null ? ` #${event.resource_id}` : ""}
                    {event.details ? ` — ${event.details}` : ""}
                  </p>
                </div>
              </div>
            ))}
          </div>
        ) : null}
      </Card>
    </div>
  );
}

export default function AuditLogPage() {
  return (
    <AppShell allow={["hod", "admin"]}>
      <div className="mx-auto max-w-5xl px-4 py-6 sm:px-6 sm:py-8 lg:px-8">
        <AuditBody />
      </div>
    </AppShell>
  );
}
