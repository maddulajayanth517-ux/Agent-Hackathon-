"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth, homeForRole } from "@/lib/auth";

export default function Home() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (loading) return;
    router.replace(user ? homeForRole(user.role) : "/login");
  }, [loading, user, router]);

  return (
    <div className="flex h-screen items-center justify-center bg-[var(--color-canvas)]">
      <div className="h-8 w-8 animate-spin rounded-full border-2 border-[var(--color-brand-500)] border-t-transparent" />
    </div>
  );
}
