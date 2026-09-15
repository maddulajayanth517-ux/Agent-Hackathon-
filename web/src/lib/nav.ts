import type { LucideIcon } from "lucide-react";
import {
  LayoutDashboard,
  Users,
  UserPlus,
  CalendarClock,
  ListChecks,
  BellRing,
  BarChart3,
  ShieldAlert,
  MessageCircle,
  Megaphone,
  FileBarChart,
  History,
} from "lucide-react";
import type { Role } from "./types";

export interface NavItem {
  label: string;
  href: string;
  icon: LucideIcon;
}

export const NAV_BY_ROLE: Record<Role, NavItem[]> = {
  student: [
    { label: "Dashboard", href: "/student/dashboard", icon: LayoutDashboard },
    { label: "My Meetings", href: "/student/meetings", icon: CalendarClock },
    { label: "Action Items", href: "/student/actions", icon: ListChecks },
    { label: "Messages", href: "/student/messages", icon: MessageCircle },
    { label: "Announcements", href: "/announcements", icon: Megaphone },
  ],
  mentor: [
    { label: "Dashboard", href: "/mentor/dashboard", icon: LayoutDashboard },
    { label: "My Mentees", href: "/mentor/mentees", icon: Users },
    { label: "Action Items", href: "/mentor/actions", icon: ListChecks },
    { label: "Alerts", href: "/mentor/alerts", icon: BellRing },
    { label: "Announcements", href: "/announcements", icon: Megaphone },
  ],
  hod: [
    { label: "Analytics", href: "/hod/dashboard", icon: BarChart3 },
    { label: "Allocations", href: "/hod/allocations", icon: UserPlus },
    { label: "Reports", href: "/reports", icon: FileBarChart },
    { label: "Audit Log", href: "/hod/audit", icon: History },
    { label: "Announcements", href: "/announcements", icon: Megaphone },
  ],
  admin: [
    { label: "Analytics", href: "/hod/dashboard", icon: BarChart3 },
    { label: "Allocations", href: "/hod/allocations", icon: UserPlus },
    { label: "Reports", href: "/reports", icon: FileBarChart },
    { label: "Audit Log", href: "/hod/audit", icon: History },
    { label: "Announcements", href: "/announcements", icon: Megaphone },
  ],
  counsellor: [
    { label: "Counselling Queue", href: "/counsellor/dashboard", icon: ShieldAlert },
    { label: "Reports", href: "/reports", icon: FileBarChart },
    { label: "Announcements", href: "/announcements", icon: Megaphone },
  ],
};
