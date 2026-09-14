"use client";

import { useState, useRef } from "react";
import { Mic, Square, Sparkles, Plus, Trash2, CheckCircle2 } from "lucide-react";
import { Card, CardHeader } from "@/components/ui/Card";
import { api, errorMessage } from "@/lib/api";
import type { ExtractedAction } from "@/lib/types";

interface DraftAction {
  title: string;
  description: string;
  owner_id: number;
  due_date: string;
}

export function MeetingForm({
  studentId,
  mentorUserId,
  studentUserId,
  onCreated,
}: {
  studentId: number;
  mentorUserId: number;
  studentUserId: number;
  onCreated: () => void;
}) {
  const now = new Date();
  const [meetingDate, setMeetingDate] = useState(now.toISOString().slice(0, 10));
  const [meetingTime, setMeetingTime] = useState(now.toTimeString().slice(0, 5));
  const [mode, setMode] = useState("in_person");
  const [agenda, setAgenda] = useState("");
  const [notes, setNotes] = useState("");
  const [studentConcerns, setStudentConcerns] = useState("");
  const [mentorObservations, setMentorObservations] = useState("");
  const [academicProgress, setAcademicProgress] = useState("");
  const [attendanceReview, setAttendanceReview] = useState("");
  const [careerDirection, setCareerDirection] = useState("");
  const [personalCircumstances, setPersonalCircumstances] = useState("");
  const [boundaryAck, setBoundaryAck] = useState(false);
  const [nextMeetingDate, setNextMeetingDate] = useState("");
  const [attendancePct, setAttendancePct] = useState("");
  const [cgpa, setCgpa] = useState("");
  const [backlogCount, setBacklogCount] = useState("");

  const [transcript, setTranscript] = useState("");
  const [listening, setListening] = useState(false);
  const [extracting, setExtracting] = useState(false);
  const [extractMessage, setExtractMessage] = useState<string | null>(null);
  const [proposed, setProposed] = useState<ExtractedAction[]>([]);
  const [actions, setActions] = useState<DraftAction[]>([]);

  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const recognitionRef = useRef<MentorSpeechRecognition | null>(null);

  function toggleVoice() {
    const globalWindow = window as unknown as {
      SpeechRecognition?: MentorSpeechRecognitionCtor;
      webkitSpeechRecognition?: MentorSpeechRecognitionCtor;
    };
    const SpeechRecognitionCtor = globalWindow.SpeechRecognition || globalWindow.webkitSpeechRecognition;
    if (!SpeechRecognitionCtor) {
      setExtractMessage("Voice dictation isn't supported in this browser. Try Chrome, or type your notes below.");
      return;
    }
    if (listening) {
      recognitionRef.current?.stop();
      setListening(false);
      return;
    }
    const recognition = new SpeechRecognitionCtor();
    recognition.continuous = true;
    recognition.interimResults = false;
    recognition.lang = "en-US";
    recognition.onresult = (event: MentorSpeechRecognitionEvent) => {
      let text = "";
      for (let i = event.resultIndex; i < event.results.length; i++) {
        text += event.results[i][0].transcript;
      }
      setTranscript((prev) => (prev ? `${prev} ${text}` : text));
    };
    recognition.onend = () => setListening(false);
    recognitionRef.current = recognition;
    recognition.start();
    setListening(true);
  }

  async function handleExtract() {
    if (!transcript.trim()) return;
    setExtracting(true);
    setExtractMessage(null);
    try {
      const result = await api.extractActions(studentId, transcript);
      setProposed(result.actions);
      if (result.source === "unavailable") setExtractMessage(result.message);
      else if (result.actions.length === 0) setExtractMessage("No clear commitments were found in this text.");
    } catch (err) {
      setExtractMessage(errorMessage(err, "AI extraction failed."));
    } finally {
      setExtracting(false);
    }
  }

  function approveProposed(index: number) {
    const item = proposed[index];
    setActions((prev) => [
      ...prev,
      {
        title: item.title,
        description: item.description ?? "",
        owner_id: item.owner_hint === "student" ? studentUserId : mentorUserId,
        due_date: item.due_date ?? "",
      },
    ]);
    setProposed((prev) => prev.filter((_, i) => i !== index));
  }

  function rejectProposed(index: number) {
    setProposed((prev) => prev.filter((_, i) => i !== index));
  }

  function addBlankAction() {
    setActions((prev) => [...prev, { title: "", description: "", owner_id: mentorUserId, due_date: "" }]);
  }

  function updateAction(index: number, patch: Partial<DraftAction>) {
    setActions((prev) => prev.map((a, i) => (i === index ? { ...a, ...patch } : a)));
  }

  function removeAction(index: number) {
    setActions((prev) => prev.filter((_, i) => i !== index));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!notes.trim()) {
      setSubmitError("Meeting notes are required.");
      return;
    }
    const incompleteAction = actions.find((a) => !a.title.trim() || !a.due_date);
    if (incompleteAction) {
      setSubmitError("Every action item needs a title and a due date before saving.");
      return;
    }
    setSubmitting(true);
    setSubmitError(null);
    try {
      await api.createMeeting({
        student_id: studentId,
        meeting_at: new Date(`${meetingDate}T${meetingTime}`).toISOString(),
        mode,
        agenda: agenda.trim() || null,
        notes: notes.trim(),
        student_concerns: studentConcerns.trim() || null,
        mentor_observations: mentorObservations.trim() || null,
        academic_progress: academicProgress.trim() || null,
        attendance_review: attendanceReview.trim() || null,
        career_direction: careerDirection.trim() || null,
        personal_circumstances: personalCircumstances.trim() || null,
        recording_boundary_acknowledged: boundaryAck,
        next_meeting_at: nextMeetingDate ? new Date(`${nextMeetingDate}T10:00`).toISOString() : null,
        attendance_pct: attendancePct ? Number(attendancePct) : null,
        cgpa: cgpa ? Number(cgpa) : null,
        backlog_count: backlogCount ? Number(backlogCount) : null,
        action_items: actions.map((a) => ({
          title: a.title.trim(),
          description: a.description.trim() || null,
          owner_id: a.owner_id,
          due_date: a.due_date,
        })),
      });
      setSuccess(true);
      onCreated();
    } catch (err) {
      setSubmitError(errorMessage(err, "Could not save this meeting."));
    } finally {
      setSubmitting(false);
    }
  }

  const inputClass =
    "w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm outline-none focus:border-[var(--color-brand-500)]";
  const textareaClass = inputClass + " min-h-[70px] resize-y";

  return (
    <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
      <form onSubmit={handleSubmit} className="space-y-5 lg:col-span-2">
        <Card className="p-5">
          <h3 className="text-sm font-semibold text-[var(--color-ink)]">Meeting details</h3>
          <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-4">
            <input type="date" value={meetingDate} onChange={(e) => setMeetingDate(e.target.value)} className={inputClass} />
            <input type="time" value={meetingTime} onChange={(e) => setMeetingTime(e.target.value)} className={inputClass} />
            <select value={mode} onChange={(e) => setMode(e.target.value)} className={inputClass}>
              <option value="in_person">In person</option>
              <option value="online">Online</option>
              <option value="phone">Phone</option>
            </select>
            <input
              value={agenda}
              onChange={(e) => setAgenda(e.target.value)}
              placeholder="Agenda"
              className={inputClass}
            />
          </div>
        </Card>

        <Card className="p-5">
          <h3 className="text-sm font-semibold text-[var(--color-ink)]">Structured mentoring record</h3>
          <div className="mt-3 space-y-3">
            <textarea value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Meeting notes (required)" className={textareaClass} />
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <textarea value={academicProgress} onChange={(e) => setAcademicProgress(e.target.value)} placeholder="Academic progress" className={textareaClass} />
              <textarea value={attendanceReview} onChange={(e) => setAttendanceReview(e.target.value)} placeholder="Attendance review" className={textareaClass} />
              <textarea value={careerDirection} onChange={(e) => setCareerDirection(e.target.value)} placeholder="Career direction" className={textareaClass} />
              <textarea value={studentConcerns} onChange={(e) => setStudentConcerns(e.target.value)} placeholder="Student concerns" className={textareaClass} />
              <textarea value={mentorObservations} onChange={(e) => setMentorObservations(e.target.value)} placeholder="Mentor observations" className={textareaClass} />
              <input type="date" value={nextMeetingDate} onChange={(e) => setNextMeetingDate(e.target.value)} className={inputClass} title="Next meeting date" />
            </div>

            <div className="rounded-xl border border-[var(--color-border)] p-3">
              <p className="text-xs text-[var(--color-muted)]">
                Attendance, CGPA and backlogs normally sync in automatically from institutional records. Fill these
                in only if that feed isn&apos;t available yet — they&apos;ll be overridden by the institutional value
                the moment it is.
              </p>
              <div className="mt-2 grid grid-cols-3 gap-3">
                <input
                  type="number"
                  min={0}
                  max={100}
                  step="0.1"
                  value={attendancePct}
                  onChange={(e) => setAttendancePct(e.target.value)}
                  placeholder="Attendance %"
                  className={inputClass}
                />
                <input
                  type="number"
                  min={0}
                  max={10}
                  step="0.01"
                  value={cgpa}
                  onChange={(e) => setCgpa(e.target.value)}
                  placeholder="CGPA"
                  className={inputClass}
                />
                <input
                  type="number"
                  min={0}
                  value={backlogCount}
                  onChange={(e) => setBacklogCount(e.target.value)}
                  placeholder="Backlogs"
                  className={inputClass}
                />
              </div>
            </div>

            <div className="rounded-xl border border-dashed border-[var(--color-border)] p-3">
              <p className="text-xs text-[var(--color-muted)]">
                Record only mentoring-relevant information here. Clinical, therapy, or detailed counselling notes
                belong in confidential counselling records, not this system.
              </p>
              <textarea
                value={personalCircumstances}
                onChange={(e) => setPersonalCircumstances(e.target.value)}
                placeholder="Personal circumstances (only if disclosed and necessary for follow-up)"
                className={textareaClass + " mt-2"}
              />
              <label className="mt-2 flex items-center gap-2 text-xs text-[var(--color-muted)]">
                <input type="checkbox" checked={boundaryAck} onChange={(e) => setBoundaryAck(e.target.checked)} />
                I have recorded only information appropriate for the mentoring system.
              </label>
            </div>
          </div>
        </Card>

        <Card className="p-5">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-[var(--color-ink)]">Action items</h3>
            <button type="button" onClick={addBlankAction} className="flex items-center gap-1 text-xs font-semibold text-[var(--color-brand-600)]">
              <Plus size={14} /> Add manually
            </button>
          </div>
          <div className="mt-3 space-y-2">
            {actions.length === 0 ? (
              <p className="text-xs text-[var(--color-muted)]">
                No actions yet. Use AI Suggestions on the right, or add one manually.
              </p>
            ) : (
              actions.map((action, index) => (
                <div key={index} className="grid grid-cols-1 gap-2 rounded-lg border border-[var(--color-border)] p-3 sm:grid-cols-[1fr_auto_auto_auto]">
                  <input
                    value={action.title}
                    onChange={(e) => updateAction(index, { title: e.target.value })}
                    placeholder="Action title"
                    className={inputClass}
                  />
                  <select
                    value={action.owner_id}
                    onChange={(e) => updateAction(index, { owner_id: Number(e.target.value) })}
                    className={inputClass}
                  >
                    <option value={studentUserId}>Student</option>
                    <option value={mentorUserId}>Mentor</option>
                  </select>
                  <input
                    type="date"
                    value={action.due_date}
                    onChange={(e) => updateAction(index, { due_date: e.target.value })}
                    className={inputClass}
                  />
                  <button type="button" onClick={() => removeAction(index)} className="flex items-center justify-center rounded-lg text-[var(--color-status-high)] hover:bg-[var(--color-status-high-bg)]">
                    <Trash2 size={15} />
                  </button>
                </div>
              ))
            )}
          </div>
        </Card>

        {submitError ? (
          <p className="rounded-lg bg-[var(--color-status-high-bg)] px-3 py-2 text-xs font-medium text-[var(--color-status-high)]">
            {submitError}
          </p>
        ) : null}
        {success ? (
          <p className="flex items-center gap-2 rounded-lg bg-[var(--color-status-low-bg)] px-3 py-2 text-xs font-medium text-[var(--color-status-low)]">
            <CheckCircle2 size={14} /> Meeting saved.
          </p>
        ) : null}

        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded-xl bg-[var(--color-brand-500)] px-4 py-2.5 text-sm font-semibold text-white hover:bg-[var(--color-brand-600)] disabled:opacity-60"
        >
          {submitting ? "Saving…" : "Save meeting"}
        </button>
      </form>

      <div className="space-y-4">
        <Card className="p-5">
          <CardHeader title="AI Suggestions" subtitle="Dictate or paste notes to extract action items" />
          <div className="mt-3 space-y-3 px-0">
            <textarea
              value={transcript}
              onChange={(e) => setTranscript(e.target.value)}
              placeholder='e.g. "Ananya will complete the Python course by Friday and discuss internship options next meeting."'
              className={textareaClass + " min-h-[110px]"}
            />
            <div className="flex gap-2">
              <button
                type="button"
                onClick={toggleVoice}
                className="flex flex-1 items-center justify-center gap-1.5 rounded-lg border border-[var(--color-border)] px-3 py-2 text-xs font-semibold text-[var(--color-ink)] hover:bg-[var(--color-brand-50)]"
              >
                {listening ? <Square size={13} /> : <Mic size={13} />}
                {listening ? "Stop" : "Voice note"}
              </button>
              <button
                type="button"
                onClick={handleExtract}
                disabled={extracting || !transcript.trim()}
                className="flex flex-1 items-center justify-center gap-1.5 rounded-lg bg-[var(--color-brand-500)] px-3 py-2 text-xs font-semibold text-white hover:bg-[var(--color-brand-600)] disabled:opacity-60"
              >
                <Sparkles size={13} /> {extracting ? "Thinking…" : "Suggest actions"}
              </button>
            </div>
            {extractMessage ? <p className="text-xs text-[var(--color-muted)]">{extractMessage}</p> : null}

            {proposed.length > 0 ? (
              <div className="space-y-2 border-t border-[var(--color-border)] pt-3">
                {proposed.map((item, index) => (
                  <div key={index} className="rounded-lg border border-[var(--color-brand-100)] bg-[var(--color-brand-50)] p-2.5">
                    <p className="text-xs font-semibold text-[var(--color-ink)]">{item.title}</p>
                    <p className="text-[11px] text-[var(--color-muted)]">
                      Owner: {item.owner_hint} {item.due_date ? `· Due ${item.due_date}` : ""}
                    </p>
                    <div className="mt-1.5 flex gap-2">
                      <button
                        type="button"
                        onClick={() => approveProposed(index)}
                        className="rounded-md bg-[var(--color-status-low)] px-2 py-1 text-[11px] font-semibold text-white"
                      >
                        Approve
                      </button>
                      <button
                        type="button"
                        onClick={() => rejectProposed(index)}
                        className="rounded-md border border-[var(--color-border)] px-2 py-1 text-[11px] font-semibold text-[var(--color-muted)]"
                      >
                        Reject
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ) : null}
          </div>
        </Card>
      </div>
    </div>
  );
}
