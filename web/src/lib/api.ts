const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export class ApiError extends Error {
  status: number;
  detail: unknown;
  constructor(status: number, detail: unknown) {
    super(typeof detail === "string" ? detail : JSON.stringify(detail));
    this.status = status;
    this.detail = detail;
  }
}

/** Extracts a human-readable message from an ApiError's (often nested/object) detail. */
export function errorMessage(err: unknown, fallback = "Something went wrong."): string {
  if (!(err instanceof ApiError)) return fallback;

  const flatten = (value: unknown): string | null => {
    if (typeof value === "string") return value;
    if (Array.isArray(value)) {
      const parts = value.map((item) => flatten(item)).filter(Boolean);
      return parts.length ? parts.join("; ") : null;
    }
    if (value && typeof value === "object") {
      const obj = value as Record<string, unknown>;
      for (const key of ["detail", "message", "msg", "error"]) {
        if (key in obj) {
          const nested = flatten(obj[key]);
          if (nested) return nested;
        }
      }
    }
    return null;
  };

  return flatten(err.detail) ?? fallback;
}

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem("mentorflow_token");
}

export function setToken(token: string | null) {
  if (typeof window === "undefined") return;
  if (token) window.localStorage.setItem("mentorflow_token", token);
  else window.localStorage.removeItem("mentorflow_token");
}

async function request<T>(
  method: string,
  path: string,
  options: { json?: unknown; params?: Record<string, string | number | boolean | undefined> } = {}
): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = { Accept: "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (options.json !== undefined) headers["Content-Type"] = "application/json";

  let url = `${API_BASE_URL}${path}`;
  if (options.params) {
    const search = new URLSearchParams();
    for (const [key, value] of Object.entries(options.params)) {
      if (value !== undefined) search.set(key, String(value));
    }
    const qs = search.toString();
    if (qs) url += `?${qs}`;
  }

  let response: Response;
  try {
    response = await fetch(url, {
      method,
      headers,
      body: options.json !== undefined ? JSON.stringify(options.json) : undefined,
    });
  } catch (err) {
    throw new ApiError(503, `Backend unavailable: ${(err as Error).message}`);
  }

  if (!response.ok) {
    let detail: unknown;
    try {
      detail = await response.json();
    } catch {
      detail = await response.text();
    }
    throw new ApiError(response.status, detail);
  }

  if (response.status === 204) return undefined as T;
  const text = await response.text();
  if (!text) return undefined as T;
  return JSON.parse(text) as T;
}

export const api = {
  login: (email: string, password: string) =>
    request<{ access_token: string; token_type: string; user_id: number; role: string }>(
      "POST",
      "/auth/login",
      { json: { email, password } }
    ),

  // Dashboards
  mentorDashboard: () => request<import("./types").MentorDashboard>("GET", "/mentor/dashboard"),
  studentDashboard: () => request<import("./types").StudentDashboard>("GET", "/student/dashboard"),
  hodAnalytics: () => request<import("./types").HodAnalytics>("GET", "/hod/analytics"),
  mentorActions: (status?: string) =>
    request<import("./types").ActionItem[]>("GET", "/mentor/actions", { params: { status_filter: status } }),

  // Students / briefs
  studentBrief: (studentId: number) =>
    request<import("./types").StudentBrief>("GET", `/brief/student/${studentId}`),
  whatChanged: (studentId: number) =>
    request<import("./types").WhatChanged>("GET", `/students/${studentId}/what-changed`),
  studentDirectory: () => request<import("./types").DirectoryStudent[]>("GET", "/allocations/directory/students"),
  mentorDirectory: () =>
    request<Array<{ id: number; name: string; capacity: number; department: string }>>(
      "GET",
      "/allocations/directory/mentors"
    ),

  // Meetings & actions
  studentMeetings: (studentId: number) =>
    request<import("./types").MeetingRecord[]>("GET", `/meetings/student/${studentId}`),
  createMeeting: (payload: Record<string, unknown>) =>
    request<import("./types").MeetingRecord>("POST", "/meetings", { json: payload }),
  updateAction: (actionId: number, payload: Record<string, unknown>) =>
    request<import("./types").ActionItem>("PATCH", `/meetings/actions/${actionId}`, { json: payload }),
  extractActions: (studentId: number, transcript: string) =>
    request<{ actions: import("./types").ExtractedAction[]; source: string; message: string | null }>(
      "POST",
      "/meetings/actions/extract",
      { json: { student_id: studentId, transcript } }
    ),

  scheduledMeetings: (studentId: number, includeClosed = false) =>
    request<import("./types").ScheduledMeeting[]>("GET", `/schedules/student/${studentId}`, {
      params: { include_closed: includeClosed },
    }),
  scheduleMeeting: (payload: Record<string, unknown>) =>
    request<import("./types").ScheduledMeeting>("POST", "/schedules", { json: payload }),
  requestMeeting: (payload: Record<string, unknown>) =>
    request<import("./types").ScheduledMeeting>("POST", "/schedules/request", { json: payload }),
  updateScheduleStatus: (scheduleId: number, state: string) =>
    request<import("./types").ScheduledMeeting>("PATCH", `/schedules/${scheduleId}/status`, {
      params: { state },
    }),

  // Flags & escalations
  studentFlags: (studentId: number) => request<import("./types").Flag[]>("GET", `/flags/student/${studentId}`),
  createFlag: (payload: Record<string, unknown>) =>
    request<import("./types").Flag>("POST", "/flags", { json: payload }),
  resolveFlag: (flagId: number) => request<import("./types").Flag>("PATCH", `/flags/${flagId}/resolve`),
  myEscalations: () => request<import("./types").Escalation[]>("GET", "/escalations/mine"),
  studentEscalations: (studentId: number) =>
    request<import("./types").Escalation[]>("GET", `/escalations/student/${studentId}`),
  createEscalation: (payload: Record<string, unknown>) =>
    request<import("./types").Escalation>("POST", "/escalations", { json: payload }),
  updateEscalation: (escalationId: number, payload: Record<string, unknown>) =>
    request<import("./types").Escalation>("PATCH", `/escalations/${escalationId}`, { json: payload }),

  // Alerts
  myAlerts: (unreadOnly = false) =>
    request<import("./types").Alert[]>("GET", "/alerts/mine", { params: { unread_only: unreadOnly } }),
  markAlertRead: (alertId: number) => request<import("./types").Alert>("PATCH", `/alerts/${alertId}/read`),

  // Corrections (student record-accuracy disputes)
  studentCorrections: (studentId: number) =>
    request<import("./types").CorrectionRequest[]>("GET", `/corrections/student/${studentId}`),
  createCorrectionRequest: (payload: Record<string, unknown>) =>
    request<import("./types").CorrectionRequest>("POST", "/corrections", { json: payload }),
  updateCorrectionRequest: (correctionId: number, payload: Record<string, unknown>) =>
    request<import("./types").CorrectionRequest>("PATCH", `/corrections/${correctionId}`, { json: payload }),

  // Audit trail
  auditEvents: (resourceType?: string, limit = 100) =>
    request<import("./types").AuditEvent[]>("GET", "/audit", { params: { resource_type: resourceType, limit } }),

  // Messaging
  studentMessages: (studentId: number) =>
    request<import("./types").Message[]>("GET", `/messages/student/${studentId}`),
  sendMessage: (studentId: number, body: string) =>
    request<import("./types").Message>("POST", "/messages", { json: { student_id: studentId, body } }),

  // Announcements
  myAnnouncements: () => request<import("./types").Announcement[]>("GET", "/announcements/mine"),
  createAnnouncement: (payload: Record<string, unknown>) =>
    request<import("./types").Announcement>("POST", "/announcements", { json: payload }),

  // Reports
  complianceReport: () => request<import("./types").ComplianceReport>("GET", "/reports/compliance"),
  mentorLoadReport: () =>
    request<{ mentors: Array<Record<string, unknown>> }>("GET", "/reports/mentor-load"),

  // Allocations
  listAllocations: () => request<import("./types").AllocationResponse[]>("GET", "/allocations"),
  createAllocation: (payload: Record<string, unknown>) =>
    request<Record<string, unknown>>("POST", "/allocations", { json: payload }),
  deactivateAllocation: (allocationId: number) =>
    request<void>("DELETE", `/allocations/${allocationId}`),
  recommendAllocation: (studentId: number) =>
    request<Record<string, unknown>>("GET", `/allocations/recommend/${studentId}`),
  addStudent: (payload: Record<string, unknown>) =>
    request<Record<string, unknown>>("POST", "/allocations/directory/students", { json: payload }),
  addMentor: (payload: Record<string, unknown>) =>
    request<Record<string, unknown>>("POST", "/allocations/directory/mentors", { json: payload }),
};

export { API_BASE_URL };
