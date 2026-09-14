"use client";

import { useEffect, useRef, useState } from "react";
import { Send } from "lucide-react";
import { EmptyBlock, ErrorBlock, LoadingBlock } from "@/components/ui/States";
import { useAuth } from "@/lib/auth";
import { api, errorMessage } from "@/lib/api";
import { useStudentMessages } from "@/lib/hooks";
import { formatDateTime, titleCase } from "@/lib/format";
import { mutate } from "swr";

export function MessageThread({ studentId }: { studentId: number }) {
  const { user } = useAuth();
  const { data: messages, error, isLoading } = useStudentMessages(studentId);
  const [body, setBody] = useState("");
  const [sending, setSending] = useState(false);
  const [sendError, setSendError] = useState<string | null>(null);
  const listRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  async function send() {
    const text = body.trim();
    if (!text) return;
    setSending(true);
    setSendError(null);
    try {
      await api.sendMessage(studentId, text);
      setBody("");
      await mutate(["student-messages", studentId]);
    } catch (err) {
      setSendError(errorMessage(err, "Could not send this message."));
    } finally {
      setSending(false);
    }
  }

  if (isLoading) return <LoadingBlock label="Loading conversation…" />;
  if (error) return <ErrorBlock message={error.message} />;

  return (
    <div className="flex h-[28rem] flex-col">
      <div ref={listRef} className="flex-1 space-y-3 overflow-y-auto px-5 py-4">
        {!messages || messages.length === 0 ? (
          <EmptyBlock message="No messages yet — say hello." />
        ) : (
          messages.map((m) => {
            const mine = m.sender_id === user?.id;
            return (
              <div key={m.id} className={`flex ${mine ? "justify-end" : "justify-start"}`}>
                <div
                  className={`max-w-[75%] rounded-2xl px-4 py-2.5 text-sm ${
                    mine
                      ? "bg-[var(--color-brand-500)] text-white"
                      : "border-l-4 border-[var(--color-brand-500)] bg-[var(--color-brand-50)] text-[var(--color-ink)]"
                  }`}
                >
                  {!mine ? (
                    <p className="mb-0.5 text-[11px] font-semibold uppercase tracking-wide opacity-70">
                      {m.sender_name} · {titleCase(m.sender_role)}
                    </p>
                  ) : null}
                  <p className="whitespace-pre-wrap">{m.body}</p>
                  <p className={`mt-1 text-[10px] ${mine ? "text-white/70" : "text-[var(--color-muted)]"}`}>
                    {formatDateTime(m.created_at)}
                  </p>
                </div>
              </div>
            );
          })
        )}
      </div>
      <div className="border-t border-[var(--color-border)] p-3">
        <div className="flex items-center gap-2 rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-2">
          <input
            value={body}
            onChange={(e) => setBody(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && send()}
            placeholder="Write a message…"
            aria-label="Write a message"
            className="flex-1 border-none bg-transparent px-1 text-sm text-[var(--color-ink)] outline-none"
          />
          <button
            onClick={send}
            disabled={sending || !body.trim()}
            aria-label="Send message"
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-[var(--color-brand-500)] text-white hover:bg-[var(--color-brand-600)] disabled:opacity-50"
          >
            <Send size={15} />
          </button>
        </div>
        {sendError ? <p className="mt-1.5 text-xs text-[var(--color-status-high)]">{sendError}</p> : null}
      </div>
    </div>
  );
}
