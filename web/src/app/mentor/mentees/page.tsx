"use client";

import Link from "next/link";
import { ArrowRight, Search } from "lucide-react";
import { useState } from "react";
import { AppShell } from "@/components/AppShell";
import { Card } from "@/components/ui/Card";
import { LoadingBlock, ErrorBlock, EmptyBlock } from "@/components/ui/States";
import { useStudentDirectory } from "@/lib/hooks";
import { initials } from "@/lib/format";

function MenteesBody() {
  const { data, error, isLoading } = useStudentDirectory();
  const [query, setQuery] = useState("");

  if (isLoading) return <LoadingBlock label="Loading your mentees…" />;
  if (error) return <ErrorBlock message={error.message} />;
  if (!data) return null;

  const filtered = data.filter(
    (s) =>
      s.name.toLowerCase().includes(query.toLowerCase()) ||
      s.register_number.toLowerCase().includes(query.toLowerCase())
  );

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-semibold text-[var(--color-ink)]">My Mentees</h2>
          <p className="mt-1 text-sm text-[var(--color-muted)]">{data.length} students allocated to you</p>
        </div>
        <div className="relative w-full sm:w-64">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--color-muted)]" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search by name or register no."
            aria-label="Search mentees by name or register number"
            className="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] py-2 pl-9 pr-3 text-sm text-[var(--color-ink)] outline-none focus:border-[var(--color-brand-500)]"
          />
        </div>
      </div>

      {filtered.length === 0 ? (
        <EmptyBlock message="No mentees match your search." />
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((student) => (
            <Link key={student.id} href={`/mentor/mentees/${student.id}`}>
              <Card className="card-hover flex items-center justify-between gap-3 p-4">
                <div className="flex items-center gap-3 min-w-0">
                  <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[var(--color-brand-100)] text-sm font-semibold text-[var(--color-brand-600)]">
                    {initials(student.name)}
                  </span>
                  <div className="min-w-0">
                    <p className="truncate text-sm font-semibold text-[var(--color-ink)]">{student.name}</p>
                    <p className="truncate text-xs text-[var(--color-muted)]">
                      {student.register_number} · {student.department}
                    </p>
                  </div>
                </div>
                <ArrowRight size={15} className="shrink-0 text-[var(--color-muted)]" />
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

export default function MenteesPage() {
  return (
    <AppShell allow={["mentor", "admin"]}>
      <div className="mx-auto max-w-6xl px-4 py-6 sm:px-6 sm:py-8 lg:px-8">
        <MenteesBody />
      </div>
    </AppShell>
  );
}
