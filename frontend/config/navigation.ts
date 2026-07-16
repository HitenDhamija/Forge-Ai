import {
  LayoutDashboard,
  FolderKanban,
  GitBranch,
  BookOpen,
  Brain,
  Bot,
  Database,
  ListChecks,
  Settings,
  HelpCircle,
  GitMerge,
  Users,
  Wrench,
  Code2,



  Rocket,
  GraduationCap,
  Activity,
  Sparkles,
  Zap,
} from "lucide-react";
import type { NavigationItem } from "@/types/common";

export const mainNavigation: NavigationItem[] = [
  {
    label: "Dashboard",
    href: "/dashboard",
    icon: LayoutDashboard,
  },
  {
    label: "Projects",
    href: "/projects",
    icon: FolderKanban,
  },
  {
    label: "Repositories",
    href: "/repositories",
    icon: GitBranch,
  },
  {
    label: "Documentation",
    href: "/documentation",
    icon: BookOpen,
  },
  {
    label: "AI Workspace",
    href: "/ai",
    icon: Brain,
  },
  {
    label: "Memory",
    href: "/memory",
    icon: Database,
  },
  {
    label: "Planner",
    href: "/planner",
    icon: ListChecks,
  },
  {
    label: "Workflows",
    href: "/workflows",
    icon: GitMerge,
  },
  {
    label: "Agents",
    href: "/agents",
    icon: Bot,
  },
  {
    label: "Workforce",
    href: "/workforce",
    icon: Users,
  },
  {
    label: "Tools",
    href: "/tools",
    icon: Wrench,
  },
  {
    label: "Software Engineer",
    href: "/software-engineer",
    icon: Code2,
  },
  {
    label: "Deployment Center",
    href: "/deployment",
    icon: Rocket,
  },
  {
    label: "Learning Center",
    href: "/learning",
    icon: GraduationCap,
  },
  {
    label: "Monitoring",
    href: "/monitoring",
    icon: Activity,
  },
  {
    label: "Studio",
    href: "/studio",
    icon: Sparkles,
  },
  {
    label: "Experience",
    href: "/experience",
    icon: Zap,
  },
];

export const bottomNavigation: NavigationItem[] = [
  {
    label: "Settings",
    href: "/settings",
    icon: Settings,
  },
  {
    label: "Help & Support",
    href: "/help",
    icon: HelpCircle,
  },
];
