"use client";

import { useState } from "react";
import { CheckCircle2, XCircle } from "lucide-react";
import { Card, CardHeader } from "@/components/ui/Card";
import { StatusPill } from "@/components/ui/Badge";
import { EmptyBlock } from "@/components/ui/States";
import { api, errorMessage } from "@/lib/api";
import { useStudentCorrections } from "@/lib/hooks";
import { formatDateTime } from "@/lib/format";
import { mutate } from "swr";

export function CorrectionsPanel({ studentId }: { studentId: number }) {
  const { data: corrections, isLoading } = useStudentCorrections(studentId);
  const [notes, setNotes] = useState<Record<number, string>>({});
  const [busyId, setBusyId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function resolve(id: number, status: "resolved" | "dismissed") {
    setBusyId(id);
    setError(null);
    try {
      await api.updateCorrectionRequest(id, { status, resolution_notes: notes[id] || undefined });
      await mutate(["student-corrections", studentId]);
    } catch (err) {
      setError(errorMessage(err, "Could not update this correction request."));
    } finally {
      setBusyId(null);
    }
  }

  const open = (corrections ?? []).filter((c) => c.status === "open" || c.status === "reviewed");
  const closed = (corrections ?? []).filter((c) => c.status === "resolved" || c.status === "dismissed");

  return (
    <Card>
      <CardHeader title="Correction requests" subtitle="Raised by the student about their own mentoring record" />
      <div className="mt-3 space-y-3 px-5 pb-5">
        {isLoading ? null : open.length === 0 && closed.length === 0 ? (
          <EmptyBlock message="No correction requests from this student." />
        ) : (
          <>
            {open.map((c) => (
              <div key={c.id} className="rounded-lg border border-[var(--color-border)] p-3">
                <div className="flex items-center justify-between gap-2">
                  <p className="text-sm font-semibold text-[var(--color-ink)]">{c.field_reference}</p>
                  <StatusPill tone="warning">{c.status}</StatusPill>
                </div>
                <p className="mt-1 text-xs text-[var(--color-muted)]">{c.description}</p>
                <p className="mt-1 text-[11px] text-[var(--color-muted)]">Sent {formatDateTime(c.created_at)}</p>
                <div className="mt-2 flex flex-col gap-2 sm:flex-row">
                  <input
                    value={notes[c.id] ?? ""}
                    onChange={(e) => setNotes((prev) => ({ ...prev, [c.id]: e.target.value }))}
                    placeholder="Note back to the student (optional)"
                    className="flex-1 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-1.5 text-xs text-[var(--color-ink)]"
                  />
                  <button
                    onClick={() => resolve(c.id, "resolved")}
                    disabled={busyId === c.id}
                    className="flex shrink-0 items-center gap-1 rounded-lg bg-[var(--color-status-low-bg)] px-2.5 py-1.5 text-xs font-semibold text-[var(--color-status-low)] hover:opacity-80 disabled:opacity-50"
                  >
                    <CheckCircle2 size={13} /> Corrected
                  </button>
                  <button
                    onClick={() => resolve(c.id, "dismissed")}
                    disabled={busyId === c.id}
                    className="flex shrink-0 items-center gap-1 rounded-lg border border-[var(--color-border)] px-2.5 py-1.5 text-xs font-semibold text-[var(--color-muted)] hover:bg-[var(--color-brand-50)] disabled:opacity-50"
                  >
                    <XCircle size={13} /> No change needed
                  </button>
                </div>
              </div>
            ))}
            {closed.map((c) => (
              <div key={c.id} className="rounded-lg border border-[var(--color-border)] p-3 opacity-80">
                <div className="flex items-center justify-between gap-2">
                  <p className="text-sm font-medium text-[var(--color-ink)]">{c.field_reference}</p>
                  <StatusPill tone={c.status === "resolved" ? "success" : "neutral"}>{c.status}</StatusPill>
                </div>
                <p className="mt-1 text-xs text-[var(--color-muted)]">{c.description}</p>
                {c.resolution_notes ? <p className="mt-1 text-xs text-[var(--color-brand-600)]">{c.resolution_notes}</p> : null}
              </div>
            ))}
          </>
        )}
        {error ? <p className="text-xs text-[var(--color-status-high)]">{error}</p> : null}
      </div>
    </Card>
  );
}
