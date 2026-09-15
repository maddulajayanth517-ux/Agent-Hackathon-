export type Role = "admin" | "hod" | "mentor" | "student" | "counsellor";

export interface AuthUser {
  id: number;
  role: Role;
  email: string;
}

export type RiskLevel = "low" | "medium" | "high" | "critical";

export type ActionStatus = "open" | "in_progress" | "completed" | "overdue" | "cancelled";

export interface ActionItem {
  id: number;
  meeting_id?: number;
  student_id: number;
  student_name?: string;
  owner_id: number;
  title: string;
  description: string | null;
  due_date: string | null;
  status: ActionStatus;
  completed_at: string | null;
}

export interface StudentBrief {
  student: {
    id: number;
    user_id: number;
    name: string | null;
    email: string | null;
    register_number: string;
    department: string;
    year: number;
    section: string | null;
  };
  mentor: {
    id: number;
    name: string | null;
    email: string | null;
    department: string;
    specialization: string | null;
  } | null;
  summary: {
    total_meetings: number;
    total_actions: number;
    open_actions: number;
    overdue_actions: number;
    completed_actions: number;
    completion_percentage: number;
  };
  latest_meeting: {
    id: number;
    meeting_at: string;
    mode: string;
    agenda: string | null;
    notes: string;
    student_concerns: string | null;
    mentor_observations: string | null;
    next_meeting_at: string | null;
  } | null;
  action_items: ActionItem[];
  key_changes: string[];
  open_concerns: string[];
  pending_actions: string[];
  discussion_points: string[];
  source: string;
  warning?: string;
  risk: {
    score: number;
    level: RiskLevel;
    alerts: string[];
    evidence: string[];
  };
  recommendations: string[];
  next_steps: string[];
  institutional_context?: {
    profile: Record<string, unknown>;
    open_flags: Record<string, unknown>[];
  };
  generated_at: string;
}

export interface WhatChanged {
  student_id: number;
  since_last_meeting_at: string | null;
  metric_changes: Array<{
    label: string;
    from: number;
    to: number;
    unit: string;
    direction: "up" | "down" | "flat";
  }>;
  new_signals: string[];
  actions_completed_since_last_meeting: string[];
  still_open_actions: Array<{ title: string; due_date: string | null; status: ActionStatus }>;
  has_baseline: boolean;
}

export interface MentorDashboard {
  mentor: { id: number; user_id: number; department: string };
  counts: {
    total_mentees: number;
    meetings_today: number;
    open_actions: number;
    new_alerts: number;
  };
  priority_queue: Array<{
    student_id: number;
    name: string;
    register_number: string;
    risk_level: RiskLevel;
    risk_score: number;
    top_issue: string;
    last_contact_days: number | null;
    recommended_action: string;
  }>;
  upcoming_meetings: Array<{
    id: number;
    student_id: number;
    student_name: string;
    scheduled_for: string;
    mode: string;
    agenda: string | null;
  }>;
  recent_alerts: Array<{
    id: number;
    student_id: number;
    title: string;
    body: string;
    severity: string;
    created_at: string;
    read_at: string | null;
  }>;
  generated_at: string;
}

export interface StudentDashboard {
  student: { id: number; name: string | null; register_number: string; department: string; year: number };
  mentor: { id: number; name: string | null; email: string | null } | null;
  next_meeting: { id: number; scheduled_for: string; mode: string; agenda: string | null } | null;
  counts: { pending_actions: number; completed_actions: number };
  profile_snapshot: { attendance_pct: number | null; cgpa: number | null; backlog_count: number | null };
  risk_level: RiskLevel;
  open_actions: Array<{ id: number; title: string; due_date: string | null; status: ActionStatus }>;
  generated_at: string;
}

export interface HodAnalytics {
  totals: {
    total_mentors: number;
    total_mentees: number;
    open_escalations: number;
    overdue_actions: number;
  };
  mentor_workload: Array<{
    mentor_id: number;
    name: string;
    active_students: number;
    capacity: number;
    utilization_percent: number;
  }>;
  student_status_distribution: Record<RiskLevel, number>;
  escalations_by_destination: Record<string, number>;
  generated_at: string;
}

export interface ComplianceReport {
  report: string;
  generated_at: string;
  metrics: {
    active_students: number;
    active_allocations: number;
    total_meetings: number;
    scheduled_meetings: number;
    completed_scheduled_meetings: number;
    missed_scheduled_meetings: number;
    students_with_meetings: number;
    meeting_coverage_percent: number;
    required_frequency_days: number;
    frequency_compliant_allocations: number;
    frequency_overdue_allocations: number;
    frequency_compliance_percent: number;
    open_actions: number;
    overdue_actions: number;
    completed_actions: number;
    action_completion_rate_percent: number;
    active_flags: number;
    open_escalations: number;
  };
}

export interface Escalation {
  id: number;
  student_id: number;
  raised_by: number;
  assigned_to: number | null;
  destination: string;
  queue_id: number | null;
  severity: RiskLevel;
  reason: string;
  status: "open" | "acknowledged" | "resolved" | "closed";
  resolution_notes: string | null;
  created_at: string;
  resolved_at: string | null;
  priority: string;
  routing_explanation: string;
}

export type ScheduledMeetingStatus = "requested" | "scheduled" | "completed" | "cancelled" | "missed";

export interface ScheduledMeeting {
  id: number;
  student_id: number;
  mentor_id: number;
  scheduled_for: string;
  mode: string;
  agenda: string | null;
  status: ScheduledMeetingStatus;
  completed_meeting_id: number | null;
  created_by: number;
  created_at: string;
}

export type CorrectionStatus = "open" | "reviewed" | "resolved" | "dismissed";

export interface CorrectionRequest {
  id: number;
  student_id: number;
  meeting_id: number | null;
  field_reference: string;
  description: string;
  status: CorrectionStatus;
  resolution_notes: string | null;
  created_at: string;
  resolved_by: number | null;
  resolved_at: string | null;
}

export interface Message {
  id: number;
  student_id: number;
  sender_id: number;
  sender_name: string;
  sender_role: string;
  body: string;
  created_at: string;
}

export type AnnouncementScope = "all" | "mentors" | "students" | "my_mentees";

export interface Announcement {
  id: number;
  author_id: number;
  author_name: string;
  author_role: string;
  scope: AnnouncementScope;
  title: string;
  body: string;
  created_at: string;
}

export interface AuditEvent {
  id: number;
  actor_id: number | null;
  actor_name: string;
  action: string;
  resource_type: string;
  resource_id: number | null;
  details: string | null;
  created_at: string;
}

export interface Alert {
  id: number;
  student_id: number;
  recipient_id: number;
  flag_id: number | null;
  severity: string;
  title: string;
  body: string;
  channel: string;
  read_at: string | null;
  actioned_at: string | null;
  created_at: string;
}

export interface Flag {
  id: number;
  student_id: number;
  created_by: number;
  severity: RiskLevel;
  category: string;
  description: string;
  is_active: boolean;
  created_at: string;
}

export interface MeetingRecord {
  id: number;
  student_id: number;
  mentor_id: number;
  meeting_at: string;
  mode: string;
  agenda: string | null;
  notes: string;
  student_concerns: string | null;
  mentor_observations: string | null;
  academic_progress: string | null;
  attendance_review: string | null;
  personal_circumstances: string | null;
  career_direction: string | null;
  recording_boundary_acknowledged: boolean;
  next_meeting_at: string | null;
  created_by: number;
  created_at: string;
  action_items: ActionItem[];
}

export interface DirectoryStudent {
  id: number;
  name: string;
  register_number: string;
  department: string;
}

export interface AllocationResponse {
  id: number;
  student_id: number;
  mentor_id: number;
  allocated_at: string;
  is_active: boolean;
  allocation_reason: string;
  reallocated_from_mentor_id: number | null;
  ended_at: string | null;
}

export interface MentorDirectoryEntry {
  id: number;
  name: string;
  capacity: number;
  department: string;
}

export interface ExtractedAction {
  title: string;
  description: string | null;
  owner_hint: string;
  due_date: string | null;
}
