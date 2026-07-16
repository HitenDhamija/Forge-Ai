"use client";

import * as React from "react";
import {
  Clock,
  ChevronDown,
  ChevronRight,
  AlertTriangle,
  CheckCircle2,
  Circle,
  Ban,
  SkipForward,
  Paperclip,
  GitBranch,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { Task, ComplexityLevel, TaskPriority, TaskStatus } from "@/types/planner";

interface TaskTimelineProps {
  tasks: Task[];
  selectedTask: Task | null;
  onSelectTask: (task: Task) => void;
}

const COMPLEXITY_CONFIG: Record<
  ComplexityLevel,
  { label: string; color: string; bgColor: string }
> = {
  simple: {
    label: "Simple",
    color: "text-success",
    bgColor: "bg-success/20",
  },
  medium: {
    label: "Medium",
    color: "text-warning",
    bgColor: "bg-warning/20",
  },
  complex: {
    label: "Complex",
    color: "text-danger",
    bgColor: "bg-danger/20",
  },
  very_complex: {
    label: "Very Complex",
    color: "text-danger",
    bgColor: "bg-danger/30",
  },
};

const PRIORITY_CONFIG: Record<
  TaskPriority,
  { label: string; color: string; bgColor: string }
> = {
  low: {
    label: "Low",
    color: "text-text-muted",
    bgColor: "bg-surface-hover",
  },
  medium: {
    label: "Medium",
    color: "text-accent",
    bgColor: "bg-accent/20",
  },
  high: {
    label: "High",
    color: "text-warning",
    bgColor: "bg-warning/20",
  },
  critical: {
    label: "Critical",
    color: "text-danger",
    bgColor: "bg-danger/20",
  },
};

const STATUS_CONFIG: Record<
  TaskStatus,
  { icon: React.ReactNode; color: string; label: string }
> = {
  pending: {
    icon: <Circle className="h-4 w-4" />,
    color: "text-text-muted",
    label: "Pending",
  },
  in_progress: {
    icon: <Clock className="h-4 w-4 text-accent animate-pulse" />,
    color: "text-accent",
    label: "In Progress",
  },
  completed: {
    icon: <CheckCircle2 className="h-4 w-4 text-success" />,
    color: "text-success",
    label: "Completed",
  },
  blocked: {
    icon: <Ban className="h-4 w-4 text-danger" />,
    color: "text-danger",
    label: "Blocked",
  },
  skipped: {
    icon: <SkipForward className="h-4 w-4 text-text-muted" />,
    color: "text-text-muted",
    label: "Skipped",
  },
};

function TaskItem({
  task,
  isSelected,
  isExpanded,
  onToggle,
  onSelect,
}: {
  task: Task;
  isSelected: boolean;
  isExpanded: boolean;
  onToggle: () => void;
  onSelect: () => void;
}) {
  const complexity = COMPLEXITY_CONFIG[task.complexity];
  const priority = PRIORITY_CONFIG[task.priority];
  const status = STATUS_CONFIG[task.status];
  const hasDeps = task.dependencies.length > 0;

  return (
    <div className="relative group">
      <div className="absolute left-6 top-0 bottom-0 w-px bg-border" />

      <div
        className={cn(
          "relative flex items-start space-x-3 pl-3 pr-2 py-3 rounded-lg transition-colors cursor-pointer",
          isSelected
            ? "bg-accent/10 border border-accent/30"
            : "hover:bg-surface-hover"
        )}
        onClick={onSelect}
      >
        <div
          className={cn(
            "relative z-10 mt-1 flex items-center justify-center h-6 w-6 rounded-full border-2 bg-bg",
            isSelected ? "border-accent" : "border-border"
          )}
        >
          {status.icon}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between space-x-2">
            <div className="flex items-center space-x-2 min-w-0">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onToggle();
                }}
                className="text-text-muted hover:text-text shrink-0"
              >
                {isExpanded ? (
                  <ChevronDown className="h-4 w-4" />
                ) : (
                  <ChevronRight className="h-4 w-4" />
                )}
              </button>
              <span className="text-xs font-mono text-text-muted">
                {task.id}
              </span>
              <span className="text-sm font-medium text-text truncate">
                {task.title}
              </span>
            </div>

            <div className="flex items-center space-x-2 shrink-0">
              {task.estimated_time_minutes !== null && (
                <span className="text-xs text-text-muted flex items-center">
                  <Clock className="h-3 w-3 mr-1" />
                  {task.estimated_time_minutes}m
                </span>
              )}
              <Badge
                variant="secondary"
                className={cn(
                  "text-xs",
                  complexity.bgColor,
                  complexity.color
                )}
              >
                {complexity.label}
              </Badge>
              <Badge
                variant="secondary"
                className={cn("text-xs", priority.bgColor, priority.color)}
              >
                {priority.label}
              </Badge>
            </div>
          </div>

          {isExpanded && (
            <div className="mt-3 space-y-3 text-sm">
              <p className="text-text-muted">{task.description}</p>

              {task.files_affected.length > 0 && (
                <div className="space-y-1">
                  <span className="text-xs font-medium text-text-muted uppercase tracking-wide flex items-center">
                    <Paperclip className="h-3 w-3 mr-1" />
                    Files Affected
                  </span>
                  <div className="flex flex-wrap gap-1">
                    {task.files_affected.map((file) => (
                      <Badge
                        key={file}
                        variant="outline"
                        className="text-xs font-mono"
                      >
                        {file}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              {hasDeps && (
                <div className="space-y-1">
                  <span className="text-xs font-medium text-text-muted uppercase tracking-wide flex items-center">
                    <GitBranch className="h-3 w-3 mr-1" />
                    Dependencies
                  </span>
                  <div className="flex flex-wrap gap-1">
                    {task.dependencies.map((dep) => (
                      <Badge
                        key={dep}
                        variant="secondary"
                        className="text-xs font-mono"
                      >
                        {dep}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              {task.required_skills.length > 0 && (
                <div className="space-y-1">
                  <span className="text-xs font-medium text-text-muted uppercase tracking-wide">
                    Required Skills
                  </span>
                  <div className="flex flex-wrap gap-1">
                    {task.required_skills.map((skill) => (
                      <Badge key={skill} variant="default" className="text-xs">
                        {skill}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              {task.notes && (
                <div className="rounded-md bg-surface-hover p-3 text-xs text-text-muted">
                  <AlertTriangle className="h-3 w-3 inline mr-1" />
                  {task.notes}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export function TaskTimeline({
  tasks,
  selectedTask,
  onSelectTask,
}: TaskTimelineProps) {
  const [expandedTasks, setExpandedTasks] = React.useState<Set<string>>(
    new Set()
  );

  const toggleExpanded = (taskId: string) => {
    setExpandedTasks((prev) => {
      const next = new Set(prev);
      if (next.has(taskId)) {
        next.delete(taskId);
      } else {
        next.add(taskId);
      }
      return next;
    });
  };

  const expandAll = () => {
    setExpandedTasks(new Set(tasks.map((t) => t.id)));
  };

  const collapseAll = () => {
    setExpandedTasks(new Set());
  };

  if (tasks.length === 0) {
    return (
      <div className="flex items-center justify-center py-12 text-text-muted">
        <p className="text-sm">No tasks in this plan</p>
      </div>
    );
  }

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-medium text-text-muted uppercase tracking-wide">
          {tasks.length} Tasks
        </span>
        <div className="flex items-center space-x-2">
          <button
            onClick={expandAll}
            className="text-xs text-accent hover:text-accent/80"
          >
            Expand All
          </button>
          <span className="text-text-muted">|</span>
          <button
            onClick={collapseAll}
            className="text-xs text-accent hover:text-accent/80"
          >
            Collapse All
          </button>
        </div>
      </div>

      <div className="space-y-1">
        {tasks.map((task) => (
          <TaskItem
            key={task.id}
            task={task}
            isSelected={selectedTask?.id === task.id}
            isExpanded={expandedTasks.has(task.id)}
            onToggle={() => toggleExpanded(task.id)}
            onSelect={() => onSelectTask(task)}
          />
        ))}
      </div>
    </div>
  );
}
