"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  FolderKanban,
  Brain,
  Bot,
  ArrowRight,
  Plus,
  Activity,
  Users,
  Zap,
  Shield,
  CheckCircle2,
  AlertTriangle,
  XCircle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { PageHeader } from "@/components/layouts/page-header";
import { apiClient } from "@/services/api";

interface StatItem {
  label: string;
  value: string;
  change: string;
  icon: any;
  color: string;
}

interface ActivityItem {
  id: string;
  action: string;
  name: string;
  time: string;
  icon: string;
}

interface HealthSummary {
  totalWorkflows: number;
  completedTasks: number;
  failedTasks: number;
  totalTasks: number;
  securityFindings: number;
  qualityIssues: number;
}

const quickActions = [
  {
    label: "New Project",
    href: "/projects/new",
    icon: Plus,
    description: "Start a new project",
  },
  {
    label: "Import Repository",
    href: "/repositories",
    icon: Plus,
    description: "Import code from Git, ZIP, or folder",
  },
  {
    label: "View Documentation",
    href: "/documentation",
    icon: Users,
    description: "Learn how to use ForgeAI",
  },
  {
    label: "Run AI Agent",
    href: "/agents",
    icon: Zap,
    description: "Assign tasks to your AI team",
  },
];

function timeAgo(dateStr: string): string {
  const now = new Date();
  const date = new Date(dateStr);
  const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);
  if (seconds < 60) return "just now";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days === 1) return "1 day ago";
  return `${days} days ago`;
}

export default function DashboardPage() {
  const [stats, setStats] = useState<StatItem[]>([
    { label: "Total Projects", value: "0", change: "Loading...", icon: FolderKanban, color: "text-accent" },
    { label: "Active AI Models", value: "0", change: "Loading...", icon: Brain, color: "text-text-muted" },
    { label: "Running Agents", value: "0", change: "Loading...", icon: Bot, color: "text-text-muted" },
    { label: "API Calls", value: "0", change: "Loading...", icon: Activity, color: "text-success" },
  ]);
  const [recentActivity, setRecentActivity] = useState<ActivityItem[]>([]);
  const [loadingActivity, setLoadingActivity] = useState(true);
  const [health, setHealth] = useState<HealthSummary>({ totalWorkflows: 0, completedTasks: 0, failedTasks: 0, totalTasks: 0, securityFindings: 0, qualityIssues: 0 });

  useEffect(() => {
    const fetchDashboardData = async () => {
      // Fetch projects count
      let projectCount = 0;
      try {
        const projectsRes = await apiClient.get<any>("/projects");
        const projectsData = projectsRes.data?.data ?? projectsRes.data;
        projectCount = Array.isArray(projectsData) ? projectsData.length : 0;
      } catch {}

      // Fetch agent metrics
      let agentMetrics = { total_agents: 0, running_tasks: 0, completed_tasks: 0 };
      try {
        const metricsRes = await apiClient.get<any>("/agents/metrics/overview");
        agentMetrics = metricsRes.data?.data ?? metricsRes.data ?? agentMetrics;
      } catch {}

      // Fetch workflow health summary
      let healthSummary: HealthSummary = { totalWorkflows: 0, completedTasks: 0, failedTasks: 0, totalTasks: 0, securityFindings: 0, qualityIssues: 0 };
      try {
        const wfRes = await apiClient.get<any>("/workflows");
        const workflows = Array.isArray(wfRes.data?.data) ? wfRes.data.data : (Array.isArray(wfRes.data) ? wfRes.data : []);
        healthSummary.totalWorkflows = workflows.length;
        for (const wf of workflows) {
          for (const task of wf.tasks || []) {
            healthSummary.totalTasks++;
            if (task.status === "completed") healthSummary.completedTasks++;
            if (task.status === "failed") healthSummary.failedTasks++;
            const result = task.result || "";
            if (result.includes("HIGH:") || result.includes("ERROR:")) healthSummary.securityFindings++;
            if (result.includes("WARNING:") || result.includes("INFO:")) healthSummary.qualityIssues++;
          }
        }
      } catch {}

      setHealth(healthSummary);

      setStats([
        { label: "Total Projects", value: String(projectCount), change: "All time", icon: FolderKanban, color: "text-accent" },
        { label: "Active AI Models", value: "0", change: "Connected via Ollama", icon: Brain, color: "text-text-muted" },
        { label: "Running Agents", value: String(agentMetrics.running_tasks || 0), change: `${agentMetrics.total_agents || 0} total agents`, icon: Bot, color: "text-text-muted" },
        { label: "Tasks Completed", value: String(agentMetrics.completed_tasks || 0), change: "All time", icon: Activity, color: "text-success" },
      ]);

      // Fetch activity
      let activities: ActivityItem[] = [];
      try {
        const rawData = await apiClient.get<any>("/experience/activity?limit=10");
        const actList = Array.isArray(rawData) ? rawData : (rawData?.data ?? []);
        activities = actList.map((a: any) => ({
          id: a.id,
          action: a.action || a.type || "Activity",
          name: a.title || a.description || "",
          time: a.timestamp ? timeAgo(a.timestamp) : "",
          icon: a.icon || "Activity",
        }));
      } catch {}

      setRecentActivity(activities);
      setLoadingActivity(false);
    };

    fetchDashboardData();
  }, []);

  return (
    <div>
      <PageHeader
        title="Dashboard"
        description="Welcome back! Here's an overview of your workspace."
        actions={
          <Link href="/projects/new">
            <Button leftIcon={<Plus className="h-4 w-4" />}>New Project</Button>
          </Link>
        }
      />

      {/* Stats Grid */}
      <div className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => {
          const Icon = stat.icon;
          return (
            <Card key={stat.label}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-text-muted">
                  {stat.label}
                </CardTitle>
                <Icon className={`h-4 w-4 ${stat.color}`} />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stat.value}</div>
                <p className="text-xs text-text-muted">{stat.change}</p>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Health Summary */}
      {health.totalWorkflows > 0 && (
        <div className="mb-8">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
              <div className="flex items-center space-x-2">
                <Shield className="h-5 w-5 text-accent" />
                <CardTitle className="text-base">Project Health</CardTitle>
              </div>
              <Link href="/workflows">
                <Button variant="ghost" size="sm" rightIcon={<ArrowRight className="h-4 w-4" />}>
                  View All
                </Button>
              </Link>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 sm:grid-cols-4">
                <div className="flex items-center space-x-3 rounded-lg border border-border p-3">
                  <CheckCircle2 className="h-8 w-8 text-success" />
                  <div>
                    <p className="text-2xl font-bold">{health.completedTasks}</p>
                    <p className="text-xs text-text-muted">Tasks Passed</p>
                  </div>
                </div>
                <div className="flex items-center space-x-3 rounded-lg border border-border p-3">
                  <XCircle className="h-8 w-8 text-danger" />
                  <div>
                    <p className="text-2xl font-bold">{health.failedTasks}</p>
                    <p className="text-xs text-text-muted">Tasks Failed</p>
                  </div>
                </div>
                <div className="flex items-center space-x-3 rounded-lg border border-border p-3">
                  <AlertTriangle className="h-8 w-8 text-warning" />
                  <div>
                    <p className="text-2xl font-bold">{health.qualityIssues}</p>
                    <p className="text-xs text-text-muted">Quality Issues</p>
                  </div>
                </div>
                <div className="flex items-center space-x-3 rounded-lg border border-border p-3">
                  <Shield className="h-8 w-8 text-danger" />
                  <div>
                    <p className="text-2xl font-bold">{health.securityFindings}</p>
                    <p className="text-xs text-text-muted">Security Findings</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Recent Activity */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
            <CardDescription>Your latest actions and updates</CardDescription>
          </CardHeader>
          <CardContent>
            {loadingActivity ? (
              <div className="space-y-4">
                {[...Array(3)].map((_, i) => (
                  <div key={i} className="flex items-center justify-between border-b border-border pb-4 last:border-0 last:pb-0">
                    <div className="space-y-1">
                      <div className="h-4 w-32 bg-muted animate-pulse rounded" />
                      <div className="h-3 w-24 bg-muted animate-pulse rounded" />
                    </div>
                    <div className="h-3 w-12 bg-muted animate-pulse rounded" />
                  </div>
                ))}
              </div>
            ) : recentActivity.length > 0 ? (
              <div className="space-y-4">
                {recentActivity.map((activity) => (
                  <div
                    key={activity.id}
                    className="flex items-center justify-between border-b border-border pb-4 last:border-0 last:pb-0"
                  >
                    <div>
                      <p className="text-sm font-medium">{activity.action}</p>
                      <p className="text-sm text-text-muted">{activity.name}</p>
                    </div>
                    <span className="text-xs text-text-muted">{activity.time}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-text-muted text-center py-4">
                No recent activity. Import a repository or create a project to get started.
              </p>
            )}
          </CardContent>
        </Card>

        {/* Quick Actions */}
        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
            <CardDescription>Frequently used actions</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {quickActions.map((action) => {
                const Icon = action.icon;
                return (
                  <Link
                    key={action.href}
                    href={action.href}
                    className="flex items-center justify-between rounded-lg border border-border p-3 transition-colors hover:bg-surface-hover"
                  >
                    <div className="flex items-center space-x-3">
                      <Icon className="h-5 w-5 text-text-muted" />
                      <div>
                        <p className="text-sm font-medium">{action.label}</p>
                        <p className="text-xs text-text-muted">
                          {action.description}
                        </p>
                      </div>
                    </div>
                    <ArrowRight className="h-4 w-4 text-text-muted" />
                  </Link>
                );
              })}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
