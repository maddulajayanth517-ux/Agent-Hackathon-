"use client";

import { useState } from "react";
import { Flag as FlagIcon, ShieldAlert } from "lucide-react";
import { SeverityBadge } from "@/components/ui/Badge";
import { EmptyBlock } from "@/components/ui/States";
import { api, errorMessage } from "@/lib/api";
import { useStudentFlags } from "@/lib/hooks";
import { mutate } from "swr";

const CATEGORIES = ["ACADEMIC", "ATTENDANCE", "PERSONAL", "EMOTIONAL", "FINANCIAL", "CAREER", "CONDUCT", "OTHER"];

const inputClass =
  "w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-xs outline-none focus:border-[var(--color-brand-500)]";

export function FlagsPanel({ studentId }: { studentId: number }) {
  const { data: flags, isLoading } = useStudentFlags(studentId);
  const [category, setCategory] = useState("ACADEMIC");
  const [severity, setSeverity] = useState("medium");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState<{ kind: "ok" | "err"; text: string } | null>(null);

  async function refreshAll() {
    await Promise.all([
      mutate(["student-flags", studentId]),
      mutate(["student-brief", studentId]),
      mutate(["what-changed", studentId]),
      mutate("mentor-dashboard"),
    ]);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!description.trim()) return;
    setSubmitting(true);
    setMessage(null);
    try {
      await api.createFlag({
        student_id: studentId,
        category,
        severity,
        title: title.trim() || null,
        description: description.trim(),
      });
      setTitle("");
      setDescription("");
      setMessage({ kind: "ok", text: "Flag raised — the allocated mentor has been alerted." });
      await refreshAll();
    } catch (err) {
      setMessage({ kind: "err", text: errorMessage(err, "Could not raise this flag.") });
    } finally {
      setSubmitting(false);
    }
  }

  async function handleResolve(flagId: number) {
    try {
      await api.resolveFlag(flagId);
      await refreshAll();
    } catch (err) {
      setMessage({ kind: "err", text: errorMessage(err, "Could not resolve this flag.") });
    }
  }

  return (
    <div className="space-y-3">
      {isLoading ? (
        <p className="text-xs text-[var(--color-muted)]">Loading flags…</p>
      ) : !flags || flags.length === 0 ? (
        <EmptyBlock message="No active flags for this student." />
      ) : (
        <div className="space-y-2">
          {flags.map((flag) => (
            <div key={flag.id} className="flex items-center justify-between gap-3 rounded-lg border border-[var(--color-border)] px-3 py-2.5">
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold uppercase tracking-wide text-[var(--color-muted)]">{flag.category}</span>
                  <SeverityBadge level={flag.severity} />
                </div>
                <p className="mt-0.5 truncate text-xs text-[var(--color-ink)]">{flag.description}</p>
              </div>
              <button
                onClick={() => handleResolve(flag.id)}
                className="shrink-0 rounded-lg border border-[var(--color-border)] px-2.5 py-1.5 text-[11px] font-semibold hover:bg-[var(--color-brand-50)]"
              >
                Resolve
              </button>
            </div>
          ))}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-2 border-t border-[var(--color-border)] pt-3">
        <p className="flex items-center gap-1.5 text-xs font-semibold text-[var(--color-ink)]">
          <FlagIcon size={13} /> Raise a flag
        </p>
        <div className="grid grid-cols-2 gap-2">
          <select value={category} onChange={(e) => setCategory(e.target.value)} className={inputClass}>
            {CATEGORIES.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
          <select value={severity} onChange={(e) => setSeverity(e.target.value)} className={inputClass}>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
            <option value="critical">Critical</option>
          </select>
        </div>
        <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Short title (optional)" className={inputClass} />
        <textarea
          required
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Describe the concern…"
          className={inputClass + " min-h-[60px] resize-y"}
        />
        <button
          type="submit"
          disabled={submitting}
          className="flex w-full items-center justify-center gap-1.5 rounded-lg bg-[var(--color-brand-500)] px-3 py-2 text-xs font-semibold text-white hover:bg-[var(--color-brand-600)] disabled:opacity-60"
        >
          <ShieldAlert size={13} /> Raise flag & alert mentor
        </button>
        {message ? (
          <p className={`text-xs ${message.kind === "ok" ? "text-[var(--color-status-low)]" : "text-[var(--color-status-high)]"}`}>{message.text}</p>
        ) : null}
      </form>
    </div>
  );
}
