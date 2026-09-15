"use client";

import useSWR from "swr";
import { api } from "./api";

const refreshOptions = { revalidateOnFocus: false, refreshInterval: 60_000 };

export function useMentorDashboard() {
  return useSWR("mentor-dashboard", api.mentorDashboard, refreshOptions);
}

export function useStudentDashboard() {
  return useSWR("student-dashboard", api.studentDashboard, refreshOptions);
}

export function useHodAnalytics() {
  return useSWR("hod-analytics", api.hodAnalytics, refreshOptions);
}

export function useMentorActions(status?: string) {
  return useSWR(["mentor-actions", status ?? "all"], () => api.mentorActions(status), refreshOptions);
}

export function useStudentBrief(studentId: number | null) {
  return useSWR(studentId ? ["student-brief", studentId] : null, () => api.studentBrief(studentId as number));
}

export function useWhatChanged(studentId: number | null) {
  return useSWR(studentId ? ["what-changed", studentId] : null, () => api.whatChanged(studentId as number));
}

export function useStudentDirectory(enabled = true) {
  return useSWR(enabled ? "student-directory" : null, api.studentDirectory);
}

export function useMentorDirectory() {
  return useSWR("mentor-directory", api.mentorDirectory);
}

export function useAllocations() {
  return useSWR("allocations", api.listAllocations);
}

export function useStudentMeetings(studentId: number | null) {
  return useSWR(studentId ? ["student-meetings", studentId] : null, () => api.studentMeetings(studentId as number));
}

export function useScheduledMeetings(studentId: number | null) {
  return useSWR(studentId ? ["scheduled-meetings", studentId] : null, () => api.scheduledMeetings(studentId as number));
}

export function useMyAlerts(unreadOnly = false) {
  return useSWR(["my-alerts", unreadOnly], () => api.myAlerts(unreadOnly), refreshOptions);
}

export function useMyEscalations() {
  return useSWR("my-escalations", api.myEscalations, refreshOptions);
}

export function useStudentEscalations(studentId: number | null) {
  return useSWR(studentId ? ["student-escalations", studentId] : null, () => api.studentEscalations(studentId as number));
}

export function useStudentFlags(studentId: number | null) {
  return useSWR(studentId ? ["student-flags", studentId] : null, () => api.studentFlags(studentId as number));
}

export function useComplianceReport() {
  return useSWR("compliance-report", api.complianceReport, refreshOptions);
}

export function useMentorLoadReport() {
  return useSWR("mentor-load-report", api.mentorLoadReport, refreshOptions);
}

export function useStudentCorrections(studentId: number | null) {
  return useSWR(studentId ? ["student-corrections", studentId] : null, () => api.studentCorrections(studentId as number));
}

export function useAuditEvents(resourceType?: string) {
  return useSWR(["audit-events", resourceType ?? "all"], () => api.auditEvents(resourceType), refreshOptions);
}

export function useStudentMessages(studentId: number | null) {
  return useSWR(studentId ? ["student-messages", studentId] : null, () => api.studentMessages(studentId as number), {
    revalidateOnFocus: false,
    refreshInterval: 15_000,
  });
}

export function useMyAnnouncements() {
  return useSWR("my-announcements", api.myAnnouncements, refreshOptions);
}
