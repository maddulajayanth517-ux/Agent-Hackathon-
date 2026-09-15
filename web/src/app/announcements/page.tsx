"use client";

import { useState } from "react";
import { Megaphone, Send } from "lucide-react";
import { AppShell } from "@/components/AppShell";
import { HeroBanner } from "@/components/ui/HeroBanner";
import { Card, CardHeader } from "@/components/ui/Card";
import { StatusPill } from "@/components/ui/Badge";
import { LoadingBlock, ErrorBlock, EmptyBlock } from "@/components/ui/States";
import { useAuth } from "@/lib/auth";
import { useMyAnnouncements } from "@/lib/hooks";
import { api, errorMessage } from "@/lib/api";
import { formatDateTime, titleCase } from "@/lib/format";
import { mutate } from "swr";
import type { AnnouncementScope } from "@/lib/types";

const SCOPE_LABEL: Record<AnnouncementScope, string> = {
  all: "Everyone",
  mentors: "All mentors",
  students: "All students",
  my_mentees: "My mentees",
};

const SCOPE_TONE: Record<AnnouncementScope, "neutral" | "info" | "warning"> = {
  all: "info",
  mentors: "neutral",
  students: "neutral",
  my_mentees: "warning",
};

function ComposeForm({ canPickScope }: { canPickScope: boolean }) {
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [scope, setScope] = useState<AnnouncementScope>("all");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!title.trim() || !body.trim()) return;
    setSubmitting(true);
    setError(null);
    setSuccess(false);
    try {
      await api.createAnnouncement({
        title: title.trim(),
        body: body.trim(),
        ...(canPickScope ? { scope } : {}),
      });
      setTitle("");
      setBody("");
      setSuccess(true);
      await mutate("my-announcements");
    } catch (err) {
      setError(errorMessage(err, "Could not post this announcement."));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Card className="p-5">
      <h3 className="text-sm font-semibold text-[var(--color-ink)]">Post an announcement</h3>
      <form onSubmit={handleSubmit} className="mt-3 space-y-2.5">
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Title"
          className="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm text-[var(--color-ink)]"
        />
        <textarea
          value={body}
          onChange={(e) => setBody(e.target.value)}
          placeholder="What do you want to tell them?"
          rows={3}
          className="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm text-[var(--color-ink)]"
        />
        <div className="flex flex-wrap items-center gap-2">
          {canPickScope ? (
            <select
              value={scope}
              onChange={(e) => setScope(e.target.value as AnnouncementScope)}
              className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-xs text-[var(--color-ink)]"
            >
              <option value="all">Everyone</option>
              <option value="mentors">All mentors</option>
              <option value="students">All students</option>
            </select>
          ) : (
            <span className="text-xs text-[var(--color-muted)]">Sent to your own mentees only.</span>
          )}
          <button
            type="submit"
            disabled={submitting}
            className="ml-auto inline-flex items-center gap-1.5 rounded-lg bg-[var(--color-brand-500)] px-3.5 py-2 text-xs font-semibold text-white hover:bg-[var(--color-brand-600)] disabled:opacity-60"
          >
            <Send size={13} /> Post
          </button>
        </div>
        {error ? <p className="text-xs text-[var(--color-status-high)]">{error}</p> : null}
        {success ? <p className="text-xs text-[var(--color-status-low)]">Posted.</p> : null}
      </form>
    </Card>
  );
}

function AnnouncementsBody() {
  const { user } = useAuth();
  const { data, error, isLoading } = useMyAnnouncements();
  const canCompose = user?.role === "hod" || user?.role === "admin" || user?.role === "mentor";
  const canPickScope = user?.role === "hod" || user?.role === "admin";

  return (
    <div className="space-y-6">
      <HeroBanner
        title="Announcements"
        subtitle="Institutional notices from HOD, and updates from your mentor or mentees."
      />

      {canCompose ? <ComposeForm canPickScope={canPickScope} /> : null}

      <Card>
        <CardHeader title="Recent announcements" />
        <div className="mt-3 px-5 pb-5">
          {isLoading ? (
            <LoadingBlock label="Loading announcements…" />
          ) : error ? (
            <ErrorBlock message={error.message} />
          ) : !data || data.length === 0 ? (
            <EmptyBlock message="No announcements yet." />
          ) : (
            <div className="space-y-3">
              {data.map((a) => (
                <div key={a.id} className="rounded-xl border border-[var(--color-border)] p-4">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <Megaphone size={15} className="text-[var(--color-brand-500)]" aria-hidden="true" />
                      <p className="text-sm font-semibold text-[var(--color-ink)]">{a.title}</p>
                    </div>
                    <StatusPill tone={SCOPE_TONE[a.scope]}>{SCOPE_LABEL[a.scope]}</StatusPill>
                  </div>
                  <p className="mt-1.5 text-sm text-[var(--color-ink)]">{a.body}</p>
                  <p className="mt-2 text-[11px] text-[var(--color-muted)]">
                    {a.author_name} · {titleCase(a.author_role)} · {formatDateTime(a.created_at)}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}

export default function AnnouncementsPage() {
  return (
    <AppShell>
      <div className="mx-auto max-w-3xl px-4 py-6 sm:px-6 sm:py-8 lg:px-8">
        <AnnouncementsBody />
      </div>
    </AppShell>
  );
}
