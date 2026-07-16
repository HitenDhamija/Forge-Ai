"use client";

import * as React from "react";
import {
  Layers,
  Clock,
  AlertTriangle,
  GitBranch,
  TrendingUp,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type {
  ExecutionPlan,
  ComplexityLevel,
  Task,
  Risk,
} from "@/types/planner";

interface ComplexityCardsProps {
  plan: ExecutionPlan;
}

const COMPLEXITY_CONFIG: Record<
  ComplexityLevel,
  {
    label: string;
    color: string;
    bgColor: string;
    borderColor: string;
    description: string;
  }
> = {
  simple: {
    label: "Simple",
    color: "text-success",
    bgColor: "bg-success/10",
    borderColor: "border-success/30",
    description:
      "Straightforward implementation with minimal risk and few dependencies.",
  },
  medium: {
    label: "Medium",
    color: "text-warning",
    bgColor: "bg-warning/10",
    borderColor: "border-warning/30",
    description:
      "Moderate complexity with some integration points and coordination needed.",
  },
  complex: {
    label: "Complex",
    color: "text-danger",
    bgColor: "bg-danger/10",
    borderColor: "border-danger/30",
    description:
      "Significant complexity with multiple integration points, many files affected, and notable risk.",
  },
  very_complex: {
    label: "Very Complex",
    color: "text-danger",
    bgColor: "bg-danger/20",
    borderColor: "border-danger/50",
    description:
      "High-risk implementation requiring careful coordination across many systems with potential breaking changes.",
  },
};

function getTaskComplexityBreakdown(tasks: Task[]) {
  const breakdown: Record<ComplexityLevel, number> = {
    simple: 0,
    medium: 0,
    complex: 0,
    very_complex: 0,
  };
  tasks.forEach((t) => {
    breakdown[t.complexity]++;
  });
  return breakdown;
}

function getRiskBreakdown(risks: Risk[]) {
  const breakdown = { low: 0, medium: 0, high: 0, critical: 0 };
  risks.forEach((r) => {
    breakdown[r.level]++;
  });
  return breakdown;
}

function formatDuration(minutes: number): string {
  if (minutes < 60) return `${minutes}m`;
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`;
}

export function ComplexityCards({ plan }: ComplexityCardsProps) {
  const config = COMPLEXITY_CONFIG[plan.complexity];
  const taskBreakdown = getTaskComplexityBreakdown(plan.tasks);
  const riskBreakdown = getRiskBreakdown(plan.risks);

  const highPriorityTasks = plan.tasks.filter(
    (t) => t.priority === "high" || t.priority === "critical"
  );
  const criticalRisks = plan.risks.filter((r) => r.level === "critical");
  const missingDeps = plan.dependencies.filter((d) => !d.exists);

  return (
    <div className="space-y-4">
      <div
        className={cn(
          "rounded-lg border p-4",
          config.borderColor,
          config.bgColor
        )}
      >
        <div className="flex items-center justify-between mb-2">
          <h4 className={cn("text-sm font-semibold", config.color)}>
            Overall Complexity
          </h4>
          <Badge
            variant="secondary"
            className={cn(
              "text-xs font-semibold uppercase",
              config.bgColor,
              config.color
            )}
          >
            {config.label}
          </Badge>
        </div>
        <p className="text-sm text-text-muted">{config.description}</p>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="rounded-lg border border-border bg-surface p-4">
          <div className="flex items-center space-x-2 text-text-muted mb-3">
            <Layers className="h-4 w-4" />
            <span className="text-xs font-medium uppercase tracking-wide">
              Task Breakdown
            </span>
          </div>
          <div className="space-y-2">
            {(Object.entries(taskBreakdown) as [ComplexityLevel, number][]).map(
              ([level, count]) => {
                const levelConfig = COMPLEXITY_CONFIG[level];
                const percentage =
                  plan.tasks.length > 0
                    ? Math.round((count / plan.tasks.length) * 100)
                    : 0;
                return (
                  <div key={level} className="space-y-1">
                    <div className="flex items-center justify-between text-xs">
                      <span className={levelConfig.color}>
                        {levelConfig.label}
                      </span>
                      <span className="text-text-muted">
                        {count} ({percentage}%)
                      </span>
                    </div>
                    <div className="h-1.5 bg-surface-hover rounded-full overflow-hidden">
                      <div
                        className={cn(
                          "h-full rounded-full transition-all",
                          levelConfig.color.replace("text-", "bg-")
                        )}
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                  </div>
                );
              }
            )}
          </div>
        </div>

        <div className="rounded-lg border border-border bg-surface p-4">
          <div className="flex items-center space-x-2 text-text-muted mb-3">
            <AlertTriangle className="h-4 w-4" />
            <span className="text-xs font-medium uppercase tracking-wide">
              Risk Breakdown
            </span>
          </div>
          <div className="space-y-2">
            {(
              Object.entries(riskBreakdown) as [
                "low" | "medium" | "high" | "critical",
                number,
              ][]
            ).map(([level, count]) => {
              const colors = {
                low: "text-success",
                medium: "text-warning",
                high: "text-danger",
                critical: "text-danger",
              };
              const percentage =
                plan.risks.length > 0
                  ? Math.round((count / plan.risks.length) * 100)
                  : 0;
              return (
                <div key={level} className="space-y-1">
                  <div className="flex items-center justify-between text-xs">
                    <span className={colors[level]}>
                      {level.charAt(0).toUpperCase() + level.slice(1)}
                    </span>
                    <span className="text-text-muted">
                      {count} ({percentage}%)
                    </span>
                  </div>
                  <div className="h-1.5 bg-surface-hover rounded-full overflow-hidden">
                    <div
                      className={cn(
                        "h-full rounded-full transition-all",
                        colors[level].replace("text-", "bg-")
                      )}
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-3">
        <div className="rounded-lg border border-border bg-surface p-3 text-center">
          <div className="flex items-center justify-center space-x-1 text-text-muted mb-1">
            <Clock className="h-3 w-3" />
            <span className="text-xs">Duration</span>
          </div>
          <p className="text-lg font-semibold text-text">
            {formatDuration(plan.estimated_duration_minutes)}
          </p>
        </div>
        <div className="rounded-lg border border-border bg-surface p-3 text-center">
          <div className="flex items-center justify-center space-x-1 text-text-muted mb-1">
            <TrendingUp className="h-3 w-3" />
            <span className="text-xs">High Priority</span>
          </div>
          <p
            className={cn(
              "text-lg font-semibold",
              highPriorityTasks.length > 0 ? "text-warning" : "text-success"
            )}
          >
            {highPriorityTasks.length}
          </p>
        </div>
        <div className="rounded-lg border border-border bg-surface p-3 text-center">
          <div className="flex items-center justify-center space-x-1 text-text-muted mb-1">
            <GitBranch className="h-3 w-3" />
            <span className="text-xs">Missing Deps</span>
          </div>
          <p
            className={cn(
              "text-lg font-semibold",
              missingDeps.length > 0 ? "text-danger" : "text-success"
            )}
          >
            {missingDeps.length}
          </p>
        </div>
      </div>
    </div>
  );
}
