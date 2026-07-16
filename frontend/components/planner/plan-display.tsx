"use client";

import * as React from "react";
import {
  Clock,
  Layers,
  AlertTriangle,
  GitBranch,
  Target,
  ArrowLeft,
  Brain,
  FileText,
  Check,
  Sparkles,
  ChevronDown,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { TaskTimeline } from "./task-timeline";
import { DependencyGraph } from "./dependency-graph";
import { ComplexityCards } from "./complexity-cards";
import { RiskPanel } from "./risk-panel";
import { ApprovalButton } from "./approval-button";
import { cn } from "@/lib/utils";
import type {
  ExecutionPlan,
  IntentType,
  ComplexityLevel,
  Task,
  Risk,
} from "@/types/planner";

interface PlanDisplayProps {
  plan: ExecutionPlan;
  onBack: () => void;
  onApprove: () => void;
  onRequestChanges: (feedback: string) => void;
  isApproving: boolean;
}

function FeatureCard({ task, index }: { task: Task; index: number }) {
  const [expanded, setExpanded] = React.useState(false);
  const priorityColors = {
    high: "bg-red-500/10 text-red-400 border-red-500/30",
    medium: "bg-yellow-500/10 text-yellow-400 border-yellow-500/30",
    low: "bg-green-500/10 text-green-400 border-green-500/30",
  };
  const impactColors = {
    high: "bg-purple-500/10 text-purple-400",
    medium: "bg-blue-500/10 text-blue-400",
    low: "bg-gray-500/10 text-gray-400",
  };
  const effortColors = {
    complex: "text-red-400",
    medium: "text-yellow-400",
    simple: "text-green-400",
  };

  const notesStr = task.notes || "";
  const stepsMatch = notesStr.match(/STEPS:\s*(.+?)(?=\n|$)/);
  const benefitMatch = notesStr.match(/BENEFIT:\s*(.+?)(?=\n|$)/);
  const techMatch = notesStr.match(/TECH:\s*(.+?)(?=\n|$)/);
  const categoryMatch = notesStr.match(/Category:\s*(\w+)/);
  const impactMatch = notesStr.match(/Impact:\s*(\w+)/);
  const newFilesMatch = notesStr.match(/New files:\s*(.+?)$/m);
  const steps = stepsMatch?.[1]?.split(" | ") || [];
  const benefit = benefitMatch?.[1] || "";
  const tech = techMatch?.[1] || "";
  const category = categoryMatch?.[1] || "General";
  const impact = impactMatch?.[1] || "medium";
  const newFiles = newFilesMatch?.[1]?.split(", ") || [];

  return (
    <div className="rounded-xl border border-border bg-surface hover:border-accent/30 transition-all overflow-hidden">
      <div className="p-4 cursor-pointer" onClick={() => setExpanded(!expanded)}>
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-medium text-accent bg-accent/10 px-2 py-0.5 rounded-full">
                #{index + 1}
              </span>
              <h4 className="text-base font-semibold text-text">{task.title}</h4>
              <ChevronDown className={`h-4 w-4 text-text-muted transition-transform ${expanded ? "rotate-180" : ""}`} />
            </div>
            <p className="text-sm text-text-muted mt-1">{task.description}</p>
          </div>
          <div className="flex flex-col items-end gap-1.5 shrink-0">
            <span className={`text-xs px-2 py-0.5 rounded-full border ${priorityColors[task.priority as keyof typeof priorityColors] || priorityColors.medium}`}>
              {task.priority} priority
            </span>
            <span className={`text-xs px-2 py-0.5 rounded-full ${impactColors[impact as keyof typeof impactColors] || impactColors.medium}`}>
              {impact} impact
            </span>
            <span className={`text-xs font-medium ${effortColors[task.complexity as keyof typeof effortColors] || effortColors.medium}`}>
              {task.complexity} effort
            </span>
          </div>
        </div>
        <div className="flex items-center gap-2 mt-3 pt-3 border-t border-border/50">
          <span className="text-xs text-text-muted bg-surface-hover px-2 py-0.5 rounded">{category}</span>
          <span className="text-xs text-text-muted">~{task.estimated_time_minutes}min</span>
          {task.files_affected.length > 0 && <span className="text-xs text-text-muted">{task.files_affected.length} files to modify</span>}
          {newFiles.length > 0 && <span className="text-xs text-accent">{newFiles.length} new files</span>}
        </div>
      </div>

      {expanded && (
        <div className="px-4 pb-4 space-y-3 border-t border-border/50">
          {benefit && (
            <div className="mt-3">
              <h5 className="text-xs font-semibold text-success uppercase tracking-wide mb-1">User Benefit</h5>
              <p className="text-sm text-text-muted">{benefit}</p>
            </div>
          )}
          {steps.length > 0 && (
            <div>
              <h5 className="text-xs font-semibold text-accent uppercase tracking-wide mb-2">Implementation Steps</h5>
              <div className="space-y-1.5">
                {steps.map((step, j) => (
                  <div key={j} className="flex items-start gap-2">
                    <span className="text-xs font-bold text-accent bg-accent/10 w-5 h-5 rounded-full flex items-center justify-center shrink-0 mt-0.5">
                      {j + 1}
                    </span>
                    <span className="text-sm text-text-muted">{step}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
          {tech && (
            <div>
              <h5 className="text-xs font-semibold text-warning uppercase tracking-wide mb-1">Technical Approach</h5>
              <p className="text-sm text-text-muted">{tech}</p>
            </div>
          )}
          {(task.files_affected.length > 0 || newFiles.length > 0) && (
            <div>
              <h5 className="text-xs font-semibold text-text-muted uppercase tracking-wide mb-1">Files</h5>
              <div className="flex flex-wrap gap-1">
                {task.files_affected.map((f) => (
                  <Badge key={f} variant="outline" className="text-xs font-mono">{f}</Badge>
                ))}
                {newFiles.map((f) => (
                  <Badge key={f} variant="secondary" className="text-xs font-mono text-accent">{f} (new)</Badge>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

const INTENT_CONFIG: Record<
  IntentType,
  { label: string; color: string; bgColor: string }
> = {
  coding: { label: "Coding", color: "text-accent", bgColor: "bg-accent/20" },
  debugging: {
    label: "Debugging",
    color: "text-danger",
    bgColor: "bg-danger/20",
  },
  documentation: {
    label: "Documentation",
    color: "text-success",
    bgColor: "bg-success/20",
  },
  architecture: {
    label: "Architecture",
    color: "text-warning",
    bgColor: "bg-warning/20",
  },
  testing: {
    label: "Testing",
    color: "text-success",
    bgColor: "bg-success/20",
  },
  database: {
    label: "Database",
    color: "text-warning",
    bgColor: "bg-warning/20",
  },
  deployment: {
    label: "Deployment",
    color: "text-danger",
    bgColor: "bg-danger/20",
  },
  research: {
    label: "Research",
    color: "text-text-muted",
    bgColor: "bg-surface-hover",
  },
  refactoring: {
    label: "Refactoring",
    color: "text-accent",
    bgColor: "bg-accent/20",
  },
  code_review: {
    label: "Code Review",
    color: "text-success",
    bgColor: "bg-success/20",
  },
  planning: {
    label: "Planning",
    color: "text-accent",
    bgColor: "bg-accent/20",
  },
  learning: {
    label: "Learning",
    color: "text-text-muted",
    bgColor: "bg-surface-hover",
  },
  unknown: {
    label: "Other",
    color: "text-text-muted",
    bgColor: "bg-surface-hover",
  },
};

const COMPLEXITY_CONFIG: Record<
  ComplexityLevel,
  { label: string; color: string; bgColor: string }
> = {
  simple: { label: "Simple", color: "text-success", bgColor: "bg-success/20" },
  medium: {
    label: "Medium",
    color: "text-warning",
    bgColor: "bg-warning/20",
  },
  complex: { label: "Complex", color: "text-danger", bgColor: "bg-danger/20" },
  very_complex: {
    label: "Very Complex",
    color: "text-danger",
    bgColor: "bg-danger/30",
  },
};

function formatDuration(minutes: number): string {
  if (minutes < 60) return `${minutes}m`;
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`;
}

export function PlanDisplay({
  plan,
  onBack,
  onApprove,
  onRequestChanges,
  isApproving,
}: PlanDisplayProps) {
  const [activeTab, setActiveTab] = React.useState("overview");
  const [selectedTask, setSelectedTask] = React.useState<Task | null>(null);
  const [selectedRisk, setSelectedRisk] = React.useState<Risk | null>(null);
  const [highlightedDep, setHighlightedDep] = React.useState<string | null>(
    null
  );

  const intentConfig = INTENT_CONFIG[plan.intent];
  const complexityConfig = COMPLEXITY_CONFIG[plan.complexity];

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-6 py-4 border-b border-border bg-surface">
        <div className="flex items-center space-x-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={onBack}
            leftIcon={<ArrowLeft className="h-4 w-4" />}
          >
            Back
          </Button>
          <div className="h-6 w-px bg-border" />
          <div className="flex items-center space-x-2">
            <div className="rounded-lg bg-accent/10 p-2">
              <Brain className="h-5 w-5 text-accent" />
            </div>
            <div>
              <h1 className="text-lg font-semibold text-text line-clamp-1">
                {plan.objective}
              </h1>
              <div className="flex items-center space-x-2 mt-0.5">
                <Badge
                  variant="secondary"
                  className={cn(
                    "text-xs",
                    intentConfig.bgColor,
                    intentConfig.color
                  )}
                >
                  {intentConfig.label}
                </Badge>
                <Badge
                  variant="secondary"
                  className={cn(
                    "text-xs",
                    complexityConfig.bgColor,
                    complexityConfig.color
                  )}
                >
                  {complexityConfig.label}
                </Badge>
                {plan.repository_name && (
                  <Badge variant="outline" className="text-xs">
                    {plan.repository_name}
                  </Badge>
                )}
              </div>
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-4 text-sm text-text-muted">
          <div className="flex items-center space-x-1">
            <Clock className="h-4 w-4" />
            <span>{formatDuration(plan.estimated_duration_minutes)}</span>
          </div>
          <div className="flex items-center space-x-1">
            <Layers className="h-4 w-4" />
            <span>{plan.tasks.length} tasks</span>
          </div>
          <div className="flex items-center space-x-1">
            <AlertTriangle className="h-4 w-4" />
            <span>{plan.risks.length} risks</span>
          </div>
          <div className="flex items-center space-x-1">
            <GitBranch className="h-4 w-4" />
            <span>{plan.dependencies.length} deps</span>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-hidden px-6 py-4">
        <Tabs
          value={activeTab}
          onValueChange={setActiveTab}
          className="h-full flex flex-col"
        >
          <TabsList>
            <TabsTrigger value="overview">
              <Target className="h-4 w-4 mr-2" />
              Overview
            </TabsTrigger>
            <TabsTrigger value="tasks">
              <Layers className="h-4 w-4 mr-2" />
              Tasks ({plan.tasks.length})
            </TabsTrigger>
            <TabsTrigger value="dependencies">
              <GitBranch className="h-4 w-4 mr-2" />
              Dependencies ({plan.dependencies.length})
            </TabsTrigger>
            <TabsTrigger value="risks">
              <AlertTriangle className="h-4 w-4 mr-2" />
              Risks ({plan.risks.length})
            </TabsTrigger>
            <TabsTrigger value="architecture">
              <FileText className="h-4 w-4 mr-2" />
              Architecture
            </TabsTrigger>
          </TabsList>

          <TabsContent
            value="overview"
            className="flex-1 mt-4 overflow-auto"
          >
            <div className="space-y-6">
              {/* Feature Suggestions - Prominent */}
              <div>
                <h3 className="text-lg font-semibold text-text mb-4 flex items-center gap-2">
                  <Sparkles className="h-5 w-5 text-accent" />
                  Suggested Features
                </h3>
                <div className="space-y-3">
                  {plan.tasks.map((task, i) => (
                    <FeatureCard key={task.id} task={task} index={i} />
                  ))}
                </div>
              </div>

              {/* Summary Stats */}
              <div className="grid grid-cols-3 gap-3">
                <div className="rounded-lg border border-border bg-surface p-4 text-center">
                  <p className="text-2xl font-bold text-accent">{plan.tasks.length}</p>
                  <p className="text-xs text-text-muted mt-1">Features Suggested</p>
                </div>
                <div className="rounded-lg border border-border bg-surface p-4 text-center">
                  <p className="text-2xl font-bold text-warning">
                    {formatDuration(plan.estimated_duration_minutes)}
                  </p>
                  <p className="text-xs text-text-muted mt-1">Est. Total Time</p>
                </div>
                <div className="rounded-lg border border-border bg-surface p-4 text-center">
                  <p className="text-2xl font-bold text-danger">{plan.risks.length}</p>
                  <p className="text-xs text-text-muted mt-1">Risks Identified</p>
                </div>
              </div>

              {/* Files Affected */}
              {plan.files_affected.length > 0 && (
                <div className="rounded-lg border border-border bg-surface p-4">
                  <h4 className="text-sm font-medium text-text mb-2">
                    Files That Will Be Affected
                  </h4>
                  <div className="flex flex-wrap gap-1">
                    {plan.files_affected.map((file) => (
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
            </div>
          </TabsContent>

          <TabsContent value="tasks" className="flex-1 mt-4 overflow-auto">
            <TaskTimeline
              tasks={plan.tasks}
              selectedTask={selectedTask}
              onSelectTask={setSelectedTask}
            />
          </TabsContent>

          <TabsContent
            value="dependencies"
            className="flex-1 mt-4 overflow-auto"
          >
            <DependencyGraph
              dependencies={plan.dependencies}
              tasks={plan.tasks}
              highlightedDep={highlightedDep}
              onHighlightDep={setHighlightedDep}
            />
          </TabsContent>

          <TabsContent value="risks" className="flex-1 mt-4 overflow-auto">
            <RiskPanel
              risks={plan.risks}
              onSelectRisk={setSelectedRisk}
              selectedRisk={selectedRisk}
            />
          </TabsContent>

          <TabsContent
            value="architecture"
            className="flex-1 mt-4 overflow-auto"
          >
            {plan.architecture_notes.length === 0 ? (
              <div className="flex items-center justify-center py-12 text-text-muted">
                <p className="text-sm">No architecture notes available</p>
              </div>
            ) : (
              <div className="space-y-4">
                {plan.architecture_notes.map((note, i) => {
                  const relatedTaskTitles = note.related_tasks
                    .map((taskId) => plan.tasks.find((t) => t.id === taskId)?.title)
                    .filter(Boolean);
                  return (
                    <div
                      key={`${note.category}-${i}`}
                      className="rounded-lg border border-border bg-surface p-4"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="text-sm font-semibold text-accent">
                          {note.category}
                        </h4>
                        {relatedTaskTitles.length > 0 && (
                          <div className="flex items-center space-x-1">
                            <span className="text-xs text-text-muted">
                              Related:
                            </span>
                            {relatedTaskTitles.map((title, j) => (
                              <Badge
                                key={j}
                                variant="secondary"
                                className="text-xs"
                              >
                                {title}
                              </Badge>
                            ))}
                          </div>
                        )}
                      </div>
                      <p className="text-sm text-text-muted whitespace-pre-wrap">
                        {note.content}
                      </p>
                    </div>
                  );
                })}
              </div>
            )}
          </TabsContent>
        </Tabs>
      </div>

      <div className="px-6 py-4 border-t border-border bg-surface">
        <ApprovalButton
          approvalRequired={plan.approval_required}
          onApprove={onApprove}
          onRequestChanges={onRequestChanges}
          isApproving={isApproving}
        />
      </div>
    </div>
  );
}
