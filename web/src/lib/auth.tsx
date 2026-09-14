"use client";

import { createContext, useContext, useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { api, setToken, ApiError } from "./api";
import type { AuthUser } from "./types";

interface AuthContextValue {
  user: AuthUser | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

const STORAGE_KEY = "mentorflow_user";

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    const token = window.localStorage.getItem("mentorflow_token");
    if (raw && token) {
      try {
        // One-time hydration from localStorage on mount — there is no prior
        // React state being synchronized from, so this isn't a cascading update.
        // eslint-disable-next-line react-hooks/set-state-in-effect
        setUser(JSON.parse(raw));
      } catch {
        window.localStorage.removeItem(STORAGE_KEY);
      }
    }
    setLoading(false);
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const result = await api.login(email, password);
    setToken(result.access_token);
    const authUser: AuthUser = { id: result.user_id, role: result.role as AuthUser["role"], email };
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(authUser));
    setUser(authUser);
  }, []);

  const logout = useCallback(() => {
    setToken(null);
    window.localStorage.removeItem(STORAGE_KEY);
    setUser(null);
    router.push("/login");
  }, [router]);

  return <AuthContext.Provider value={{ user, loading, login, logout }}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

export function homeForRole(role: string): string {
  switch (role) {
    case "student":
      return "/student/dashboard";
    case "mentor":
      return "/mentor/dashboard";
    case "hod":
      return "/hod/dashboard";
    case "counsellor":
      return "/counsellor/dashboard";
    case "admin":
      return "/hod/dashboard";
    default:
      return "/login";
  }
}

export { ApiError };
