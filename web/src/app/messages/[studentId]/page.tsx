"use client";

import { use } from "react";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { AppShell } from "@/components/AppShell";
import { Card, CardHeader } from "@/components/ui/Card";
import { LoadingBlock, ErrorBlock } from "@/components/ui/States";
import { MessageThread } from "@/components/mentee/MessageThread";
import { useStudentBrief } from "@/lib/hooks";

function MessagesBody({ studentId }: { studentId: number }) {
  const { data: brief, isLoading, error } = useStudentBrief(studentId);

  if (isLoading) return <LoadingBlock label="Loading conversation…" />;
  if (error) return <ErrorBlock message={error.message} />;

  return (
    <Card>
      <CardHeader
        title={brief ? `Messages with ${brief.student.name}` : "Messages"}
        subtitle={brief ? `${brief.student.register_number} · ${brief.student.department}` : undefined}
      />
      <MessageThread studentId={studentId} />
    </Card>
  );
}

export default function StudentMessagesPage({ params }: { params: Promise<{ studentId: string }> }) {
  const { studentId } = use(params);
  const id = Number(studentId);
  return (
    <AppShell allow={["mentor", "hod", "counsellor", "admin"]}>
      <div className="mx-auto max-w-3xl space-y-4 px-4 py-6 sm:px-6 sm:py-8 lg:px-8">
        <Link href="/" className="flex items-center gap-1.5 text-xs font-semibold text-[var(--color-muted)] hover:text-[var(--color-ink)]">
          <ArrowLeft size={14} /> Back
        </Link>
        <MessagesBody studentId={id} />
      </div>
    </AppShell>
  );
}
