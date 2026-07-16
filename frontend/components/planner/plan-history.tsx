"use client";

import * as React from "react";
import {
  Clock,
  Trash2,
  ChevronLeft,
  ChevronRight,
  ListChecks,
  Calendar,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { cn } from "@/lib/utils";
import type { PlanHistoryItem, IntentType, ComplexityLevel } from "@/types/planner";

interface PlanHistoryProps {
  plans: PlanHistoryItem[];
  onSelectPlan: (plan: PlanHistoryItem) => void;
  onDeletePlan: (id: string) => void;
  selectedPlanId: string | null;
  isLoading: boolean;
}

const INTENT_LABELS: Record<IntentType, string> = {
  coding: "Coding",
  debugging: "Debugging",
  documentation: "Docs",
  architecture: "Arch",
  testing: "Testing",
  database: "Database",
  deployment: "Deploy",
  research: "Research",
  refactoring: "Refactor",
  code_review: "Review",
  planning: "Planning",
  learning: "Learning",
  unknown: "Other",
};

const COMPLEXITY_COLORS: Record<ComplexityLevel, string> = {
  simple: "text-success",
  medium: "text-warning",
  complex: "text-danger",
  very_complex: "text-danger",
};

function formatDuration(minutes: number): string {
  if (minutes < 60) return `${minutes}m`;
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`;
}

function formatDate(dateStr: string): string {
  try {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  } catch {
    return dateStr;
  }
}

export function PlanHistory({
  plans,
  onSelectPlan,
  onDeletePlan,
  selectedPlanId,
  isLoading,
}: PlanHistoryProps) {
  const [isCollapsed, setIsCollapsed] = React.useState(false);

  // Auto-collapse when no plans
  React.useEffect(() => {
    if (plans.length === 0 && !isCollapsed) {
      setIsCollapsed(true);
    }
  }, [plans.length, isCollapsed]);

  if (isCollapsed) {
    return (
      <div className="w-10 border-l border-border bg-surface flex flex-col items-center py-4">
        <button
          onClick={() => setIsCollapsed(false)}
          className="p-1.5 rounded-md hover:bg-surface-hover text-text-muted hover:text-text transition-colors"
          title="Expand history"
        >
          <ChevronRight className="h-4 w-4" />
        </button>
        <div className="mt-4 space-y-2">
          {plans.slice(0, 10).map((plan, i) => (
            <button
              key={plan.id}
              onClick={() => onSelectPlan(plan)}
              className={cn(
                "w-6 h-6 rounded text-xs font-medium transition-colors",
                selectedPlanId === plan.id
                  ? "bg-accent text-white"
                  : "bg-surface-hover text-text-muted hover:text-text"
              )}
              title={plan.objective}
            >
              {i + 1}
            </button>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="w-72 border-l border-border bg-surface flex flex-col">
      <div className="flex items-center justify-between px-4 py-3 border-b border-border">
        <div className="flex items-center space-x-2">
          <Clock className="h-4 w-4 text-text-muted" />
          <span className="text-sm font-medium text-text">Plan History</span>
          <Badge variant="secondary" className="text-xs">
            {plans.length}
          </Badge>
        </div>
        <button
          onClick={() => setIsCollapsed(true)}
          className="p-1 rounded-md hover:bg-surface-hover text-text-muted hover:text-text transition-colors"
        >
          <ChevronLeft className="h-4 w-4" />
        </button>
      </div>

      <div className="flex-1 overflow-auto">
        {plans.length === 0 ? (
          <EmptyState
            icon={<ListChecks className="h-12 w-12" />}
            title="No plans yet"
            description="Generate your first execution plan to get started"
          />
        ) : (
          <div className="p-2 space-y-1">
            {plans.map((plan) => (
              <div
                key={plan.id}
                className={cn(
                  "group rounded-lg p-3 cursor-pointer transition-all",
                  selectedPlanId === plan.id
                    ? "bg-accent/10 border border-accent/30"
                    : "hover:bg-surface-hover border border-transparent"
                )}
                onClick={() => onSelectPlan(plan)}
              >
                <div className="flex items-start justify-between">
                  <p className="text-sm text-text line-clamp-2 flex-1">
                    {plan.objective}
                  </p>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onDeletePlan(plan.id);
                    }}
                    className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-danger/10 text-text-muted hover:text-danger transition-all ml-2"
                  >
                    <Trash2 className="h-3 w-3" />
                  </button>
                </div>

                <div className="flex items-center space-x-2 mt-2">
                  <Badge variant="secondary" className="text-xs">
                    {INTENT_LABELS[plan.intent]}
                  </Badge>
                  <span
                    className={cn(
                      "text-xs font-medium",
                      COMPLEXITY_COLORS[plan.complexity]
                    )}
                  >
                    {plan.complexity.replace("_", " ")}
                  </span>
                </div>

                <div className="flex items-center justify-between mt-2 text-xs text-text-muted">
                  <div className="flex items-center space-x-2">
                    <span>{plan.task_count} tasks</span>
                    <span>-</span>
                    <span>{plan.risk_count} risks</span>
                    <span>-</span>
                    <span>
                      {formatDuration(plan.estimated_duration_minutes)}
                    </span>
                  </div>
                  <span className="flex items-center">
                    <Calendar className="h-3 w-3 mr-1" />
                    {formatDate(plan.created_at)}
                  </span>
                </div>

                {plan.repository_name && (
                  <p className="text-xs text-text-muted mt-1 truncate">
                    {plan.repository_name}
                  </p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
