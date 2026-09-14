"use client";

import { AppShell } from "@/components/AppShell";
import { Card, CardHeader } from "@/components/ui/Card";
import { LoadingBlock, ErrorBlock } from "@/components/ui/States";
import { MessageThread } from "@/components/mentee/MessageThread";
import { useStudentDashboard } from "@/lib/hooks";

function MessagesBody() {
  const { data: dashboard, isLoading, error } = useStudentDashboard();

  if (isLoading) return <LoadingBlock label="Loading your conversation…" />;
  if (error) return <ErrorBlock message={error.message} />;
  if (!dashboard) return null;

  return (
    <Card>
      <CardHeader
        title="Messages"
        subtitle={dashboard.mentor ? `With ${dashboard.mentor.name} and anyone currently handling an open escalation for you` : "Your mentor will appear here once allocated"}
      />
      <MessageThread studentId={dashboard.student.id} />
    </Card>
  );
}

export default function StudentMessagesPage() {
  return (
    <AppShell allow={["student"]}>
      <div className="mx-auto max-w-3xl px-4 py-6 sm:px-6 sm:py-8 lg:px-8">
        <MessagesBody />
      </div>
    </AppShell>
  );
}
