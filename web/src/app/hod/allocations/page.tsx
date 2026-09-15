"use client";

import { useMemo, useState } from "react";
import { UserPlus, GraduationCap, Link2, Sparkles, Trash2 } from "lucide-react";
import { AppShell } from "@/components/AppShell";
import { Card, CardHeader } from "@/components/ui/Card";
import { LoadingBlock, ErrorBlock, EmptyBlock } from "@/components/ui/States";
import { api, errorMessage } from "@/lib/api";
import { useStudentDirectory, useMentorDirectory, useAllocations } from "@/lib/hooks";
import { mutate } from "swr";

const inputClass =
  "w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm outline-none focus:border-[var(--color-brand-500)]";

function AddStudentForm() {
  const [form, setForm] = useState({ full_name: "", email: "", register_number: "", department: "CSE", year: 1, section: "" });
  const [message, setMessage] = useState<{ kind: "ok" | "err"; text: string } | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setMessage(null);
    try {
      await api.addStudent({ ...form, section: form.section || null });
      setMessage({ kind: "ok", text: `Added ${form.full_name} to the student directory.` });
      setForm({ full_name: "", email: "", register_number: "", department: form.department, year: form.year, section: "" });
      await mutate("student-directory");
    } catch (err) {
      setMessage({ kind: "err", text: errorMessage(err, "Could not add this student.") });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-2.5">
      <input required placeholder="Full name" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} className={inputClass} />
      <input required type="email" placeholder="Institutional email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} className={inputClass} />
      <div className="grid grid-cols-2 gap-2.5">
        <input required placeholder="Register number" value={form.register_number} onChange={(e) => setForm({ ...form, register_number: e.target.value })} className={inputClass} />
        <input required placeholder="Department" value={form.department} onChange={(e) => setForm({ ...form, department: e.target.value })} className={inputClass} />
        <input required type="number" min={1} max={10} placeholder="Year" value={form.year} onChange={(e) => setForm({ ...form, year: Number(e.target.value) })} className={inputClass} />
        <input placeholder="Section (optional)" value={form.section} onChange={(e) => setForm({ ...form, section: e.target.value })} className={inputClass} />
      </div>
      <button type="submit" disabled={submitting} className="flex w-full items-center justify-center gap-1.5 rounded-lg bg-[var(--color-brand-500)] px-3 py-2 text-xs font-semibold text-white hover:bg-[var(--color-brand-600)] disabled:opacity-60">
        <UserPlus size={14} /> Add student
      </button>
      {message ? (
        <p className={`text-xs ${message.kind === "ok" ? "text-[var(--color-status-low)]" : "text-[var(--color-status-high)]"}`}>{message.text}</p>
      ) : null}
    </form>
  );
}

function AddMentorForm() {
  const [form, setForm] = useState({ full_name: "", email: "", department: "CSE", specialization: "", max_students: 15 });
  const [message, setMessage] = useState<{ kind: "ok" | "err"; text: string } | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setMessage(null);
    try {
      await api.addMentor({ ...form, specialization: form.specialization || null });
      setMessage({ kind: "ok", text: `Added ${form.full_name} to the mentor directory.` });
      setForm({ full_name: "", email: "", department: form.department, specialization: "", max_students: 15 });
      await mutate("mentor-directory");
    } catch (err) {
      setMessage({ kind: "err", text: errorMessage(err, "Could not add this mentor.") });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-2.5">
      <input required placeholder="Full name" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} className={inputClass} />
      <input required type="email" placeholder="Institutional email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} className={inputClass} />
      <div className="grid grid-cols-2 gap-2.5">
        <input required placeholder="Department" value={form.department} onChange={(e) => setForm({ ...form, department: e.target.value })} className={inputClass} />
        <input placeholder="Specialization (optional)" value={form.specialization} onChange={(e) => setForm({ ...form, specialization: e.target.value })} className={inputClass} />
        <input required type="number" min={1} max={500} placeholder="Max mentees" value={form.max_students} onChange={(e) => setForm({ ...form, max_students: Number(e.target.value) })} className={inputClass} />
      </div>
      <button type="submit" disabled={submitting} className="flex w-full items-center justify-center gap-1.5 rounded-lg bg-[var(--color-brand-500)] px-3 py-2 text-xs font-semibold text-white hover:bg-[var(--color-brand-600)] disabled:opacity-60">
        <UserPlus size={14} /> Add mentor
      </button>
      {message ? (
        <p className={`text-xs ${message.kind === "ok" ? "text-[var(--color-status-low)]" : "text-[var(--color-status-high)]"}`}>{message.text}</p>
      ) : null}
    </form>
  );
}

function AllocationManager() {
  const { data: students } = useStudentDirectory();
  const { data: mentors } = useMentorDirectory();
  const { data: allocations, error, isLoading } = useAllocations();
  const [studentId, setStudentId] = useState<number | "">("");
  const [mentorId, setMentorId] = useState<number | "">("");
  const [reason, setReason] = useState("INITIAL");
  const [message, setMessage] = useState<{ kind: "ok" | "err"; text: string } | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [recommending, setRecommending] = useState(false);

  const studentName = useMemo(() => new Map((students ?? []).map((s) => [s.id, s.name])), [students]);
  const mentorName = useMemo(() => new Map((mentors ?? []).map((m) => [m.id, m.name])), [mentors]);

  async function handleRecommend() {
    if (!studentId) return;
    setRecommending(true);
    setMessage(null);
    try {
      const rec = await api.recommendAllocation(studentId);
      setMentorId(rec.mentor_id as number);
      setMessage({ kind: "ok", text: `Recommended: ${rec.mentor_name} — ${rec.reason}` });
    } catch (err) {
      setMessage({ kind: "err", text: errorMessage(err, "No recommendation available.") });
    } finally {
      setRecommending(false);
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!studentId || !mentorId) return;
    setSubmitting(true);
    setMessage(null);
    try {
      await api.createAllocation({ student_id: studentId, mentor_id: mentorId, reason: reason.trim() || "INITIAL" });
      setMessage({ kind: "ok", text: "Allocation created." });
      await mutate("allocations");
    } catch (err) {
      setMessage({ kind: "err", text: errorMessage(err, "Could not create this allocation.") });
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDeactivate(id: number) {
    try {
      await api.deactivateAllocation(id);
      await mutate("allocations");
    } catch (err) {
      setMessage({ kind: "err", text: errorMessage(err, "Could not end this allocation.") });
    }
  }

  return (
    <div className="space-y-4">
      <form onSubmit={handleSubmit} className="grid grid-cols-1 gap-2.5 sm:grid-cols-[1.3fr_1fr_1fr_auto_auto]">
        <select required value={studentId} onChange={(e) => setStudentId(e.target.value ? Number(e.target.value) : "")} className={inputClass}>
          <option value="">Select student…</option>
          {students?.map((s) => (
            <option key={s.id} value={s.id}>{s.name} · {s.register_number}</option>
          ))}
        </select>
        <select required value={mentorId} onChange={(e) => setMentorId(e.target.value ? Number(e.target.value) : "")} className={inputClass}>
          <option value="">Select mentor…</option>
          {mentors?.map((m) => (
            <option key={m.id} value={m.id}>{m.name}</option>
          ))}
        </select>
        <input placeholder="Reason" value={reason} onChange={(e) => setReason(e.target.value)} className={inputClass} />
        <button
          type="button"
          onClick={handleRecommend}
          disabled={!studentId || recommending}
          className="flex items-center justify-center gap-1 rounded-lg border border-[var(--color-border)] px-3 py-2 text-xs font-semibold hover:bg-[var(--color-brand-50)] disabled:opacity-50"
        >
          <Sparkles size={13} /> Recommend
        </button>
        <button type="submit" disabled={submitting} className="flex items-center justify-center gap-1 rounded-lg bg-[var(--color-brand-500)] px-3 py-2 text-xs font-semibold text-white hover:bg-[var(--color-brand-600)] disabled:opacity-60">
          <Link2 size={13} /> Allocate
        </button>
      </form>
      {message ? (
        <p className={`text-xs ${message.kind === "ok" ? "text-[var(--color-status-low)]" : "text-[var(--color-status-high)]"}`}>{message.text}</p>
      ) : null}

      {isLoading ? (
        <LoadingBlock label="Loading allocations…" />
      ) : error ? (
        <ErrorBlock message={error.message} />
      ) : !allocations || allocations.length === 0 ? (
        <EmptyBlock message="No active allocations yet." />
      ) : (
        <div className="divide-y divide-[var(--color-border)] rounded-xl border border-[var(--color-border)]">
          {allocations.map((a) => (
            <div key={a.id} className="flex items-center justify-between gap-3 px-4 py-2.5">
              <p className="text-sm text-[var(--color-ink)]">
                <span className="font-medium">{studentName.get(a.student_id) ?? `Student #${a.student_id}`}</span>
                {" → "}
                <span className="font-medium">{mentorName.get(a.mentor_id) ?? `Mentor #${a.mentor_id}`}</span>
                <span className="ml-2 text-xs text-[var(--color-muted)]">({a.allocation_reason})</span>
              </p>
              <button onClick={() => handleDeactivate(a.id)} className="flex shrink-0 items-center gap-1 rounded-lg text-xs font-semibold text-[var(--color-status-high)] hover:bg-[var(--color-status-high-bg)] px-2 py-1">
                <Trash2 size={13} /> End
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function AllocationsPage() {
  return (
    <AppShell allow={["hod", "admin"]}>
      <div className="mx-auto max-w-5xl space-y-6 px-4 py-6 sm:px-6 sm:py-8 lg:px-8">
        <div>
          <h2 className="text-2xl font-semibold text-[var(--color-ink)]">Mentor Allocation</h2>
          <p className="mt-1 text-sm text-[var(--color-muted)]">Add students and mentors, then connect them.</p>
        </div>

        <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
          <Card className="p-5">
            <h3 className="flex items-center gap-1.5 text-sm font-semibold text-[var(--color-ink)]">
              <GraduationCap size={15} /> Add a student
            </h3>
            <div className="mt-3">
              <AddStudentForm />
            </div>
          </Card>
          <Card className="p-5">
            <h3 className="flex items-center gap-1.5 text-sm font-semibold text-[var(--color-ink)]">
              <UserPlus size={15} /> Add a mentor
            </h3>
            <div className="mt-3">
              <AddMentorForm />
            </div>
          </Card>
        </div>

        <Card>
          <CardHeader title="Allocations" subtitle="Connect a student to a mentor, or end an existing allocation" />
          <div className="mt-3 px-5 pb-5">
            <AllocationManager />
          </div>
        </Card>
      </div>
    </AppShell>
  );
}
