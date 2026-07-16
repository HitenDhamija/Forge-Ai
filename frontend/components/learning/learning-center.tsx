"use client";

import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { apiClient } from "@/services/api";
import type { FeedbackType } from "@/types/learning";
import {
  Modal,
  ModalContent,
  ModalDescription,
  ModalFooter,
  ModalHeader,
  ModalTitle,
} from "@/components/ui/modal";
import { useLearningStore } from "@/stores/learning-store";
import type {
  Experience,
  Pattern,
  Lesson,
  Recommendation,
  ExperienceType,
  OutcomeType,
  PatternType,
  LessonType,
  Severity,
  Priority,
} from "@/types/learning";
import {
  BookOpen,
  Lightbulb,
  AlertTriangle,
  Target,
  TrendingUp,
  Search,
  Filter,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  BarChart3,
  Brain,
  RefreshCw,
  ThumbsUp,
  ThumbsDown,
  Minus,
  ChevronDown,
  Sparkles,
  Zap,
  Shield,
  Database,
  Code,
  Rocket,
  Bug,
  FileText,
  Layers,
  Workflow,
  ArrowUpRight,
  Eye,
} from "lucide-react";

const EXPERIENCE_TYPE_CONFIG: Record<ExperienceType, { label: string; icon: React.ReactNode; color: string }> = {
  architecture: { label: "Architecture", icon: <Layers className="h-3.5 w-3.5" />, color: "bg-blue-500/20 text-blue-400" },
  bug_fix: { label: "Bug Fix", icon: <Bug className="h-3.5 w-3.5" />, color: "bg-red-500/20 text-red-400" },
  deployment: { label: "Deployment", icon: <Rocket className="h-3.5 w-3.5" />, color: "bg-purple-500/20 text-purple-400" },
  database: { label: "Database", icon: <Database className="h-3.5 w-3.5" />, color: "bg-cyan-500/20 text-cyan-400" },
  testing: { label: "Testing", icon: <Target className="h-3.5 w-3.5" />, color: "bg-green-500/20 text-green-400" },
  performance: { label: "Performance", icon: <Zap className="h-3.5 w-3.5" />, color: "bg-yellow-500/20 text-yellow-400" },
  security: { label: "Security", icon: <Shield className="h-3.5 w-3.5" />, color: "bg-orange-500/20 text-orange-400" },
  documentation: { label: "Documentation", icon: <FileText className="h-3.5 w-3.5" />, color: "bg-gray-500/20 text-gray-400" },
  refactoring: { label: "Refactoring", icon: <Code className="h-3.5 w-3.5" />, color: "bg-indigo-500/20 text-indigo-400" },
};

const PATTERN_TYPE_CONFIG: Record<PatternType, { label: string; icon: React.ReactNode }> = {
  architecture: { label: "Architecture", icon: <Layers className="h-3.5 w-3.5" /> },
  coding: { label: "Coding", icon: <Code className="h-3.5 w-3.5" /> },
  security: { label: "Security", icon: <Shield className="h-3.5 w-3.5" /> },
  deployment: { label: "Deployment", icon: <Rocket className="h-3.5 w-3.5" /> },
  testing: { label: "Testing", icon: <Target className="h-3.5 w-3.5" /> },
  database: { label: "Database", icon: <Database className="h-3.5 w-3.5" /> },
  frontend: { label: "Frontend", icon: <Eye className="h-3.5 w-3.5" /> },
  backend: { label: "Backend", icon: <Workflow className="h-3.5 w-3.5" /> },
};

const LESSON_TYPE_CONFIG: Record<LessonType, { label: string; icon: React.ReactNode }> = {
  failure: { label: "Failure", icon: <XCircle className="h-3.5 w-3.5" /> },
  rejection: { label: "Rejection", icon: <AlertCircle className="h-3.5 w-3.5" /> },
  regression: { label: "Regression", icon: <RefreshCw className="h-3.5 w-3.5" /> },
  violation: { label: "Violation", icon: <AlertTriangle className="h-3.5 w-3.5" /> },
  security_issue: { label: "Security Issue", icon: <Shield className="h-3.5 w-3.5" /> },
  performance_issue: { label: "Performance Issue", icon: <Zap className="h-3.5 w-3.5" /> },
};

const SEVERITY_CONFIG: Record<Severity, { label: string; variant: "destructive" | "warning" | "secondary" | "default" }> = {
  critical: { label: "Critical", variant: "destructive" },
  high: { label: "High", variant: "warning" },
  medium: { label: "Medium", variant: "secondary" },
  low: { label: "Low", variant: "default" },
};

const PRIORITY_CONFIG: Record<Priority, { label: string; variant: "destructive" | "warning" | "secondary" | "default" }> = {
  high: { label: "High", variant: "destructive" },
  medium: { label: "Medium", variant: "warning" },
  low: { label: "Low", variant: "default" },
};

function getOutcomeBadge(outcome: OutcomeType) {
  switch (outcome) {
    case "success":
      return <Badge variant="success"><CheckCircle className="mr-1 h-3 w-3" />Success</Badge>;
    case "failure":
      return <Badge variant="destructive"><XCircle className="mr-1 h-3 w-3" />Failure</Badge>;
    case "partial":
      return <Badge variant="warning"><Minus className="mr-1 h-3 w-3" />Partial</Badge>;
  }
}

function getConfidenceColor(confidence: number): string {
  if (confidence >= 0.8) return "text-green-400";
  if (confidence >= 0.5) return "text-yellow-400";
  return "text-red-400";
}

function getConfidenceVariant(confidence: number): "success" | "warning" | "destructive" {
  if (confidence >= 0.8) return "success";
  if (confidence >= 0.5) return "warning";
  return "destructive";
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function formatRelativeTime(dateStr: string): string {
  const now = new Date();
  const date = new Date(dateStr);
  const diffMs = now.getTime() - date.getTime();
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  if (diffHours < 1) return "just now";
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return formatDate(dateStr);
}

export function LearningCenter() {
  const {
    experiences,
    patterns,
    lessons,
    recommendations,
    stats,
    growth,
    tasks,
    isLoading,
    error,
    processWorkflow,
    fetchExperiences,
    fetchPatterns,
    fetchRecommendations,
    fetchStats,
    fetchGrowth,
    fetchTasks,
    submitFeedback,
    clearError,
  } = useLearningStore();

  const [activeTab, setActiveTab] = useState("overview");
  const [experienceFilter, setExperienceFilter] = useState<ExperienceType | "">("");
  const [outcomeFilter, setOutcomeFilter] = useState<OutcomeType | "">("");
  const [patternSearch, setPatternSearch] = useState("");
  const [patternTypeFilter, setPatternTypeFilter] = useState<PatternType | "">("");
  const [showWorkflowModal, setShowWorkflowModal] = useState(false);
  const [projects, setProjects] = useState<{ id: string; name: string; description?: string; frameworks?: string[]; languages?: string[] }[]>([]);
  const [workflowForm, setWorkflowForm] = useState({
    workflow_id: "",
    repository_id: "",
    title: "",
    description: "",
    outcome: "success",
    files_changed: "",
    technologies: "",
  });
  const [isProcessing, setIsProcessing] = useState(false);
  const [feedbackForm, setFeedbackForm] = useState<{
    experienceId: string;
    feedbackType: string;
    comment: string;
  } | null>(null);

  useEffect(() => {
    fetchStats();
    fetchGrowth();
    fetchTasks();
  }, [fetchStats, fetchGrowth, fetchTasks]);

  useEffect(() => {
    if (showWorkflowModal) {
      apiClient.get("/projects").then((res: any) => {
        const data = res.data;
        const list = Array.isArray(data) ? data : data?.data || [];
        setProjects(list);
      }).catch(() => {});
    }
  }, [showWorkflowModal]);

  useEffect(() => {
    if (activeTab === "overview") {
      fetchExperiences({ limit: 5 });
      fetchPatterns({ limit: 5 });
    }
  }, [activeTab, fetchExperiences, fetchPatterns]);

  const handleTabChange = useCallback(
    (tab: string) => {
      setActiveTab(tab);
      switch (tab) {
        case "experiences":
          fetchExperiences({
            experience_type: experienceFilter || undefined,
            outcome: outcomeFilter || undefined,
            limit: 50,
          });
          break;
        case "patterns":
          fetchPatterns({
            pattern_type: patternTypeFilter || undefined,
            limit: 50,
          });
          break;
        case "recommendations":
          fetchRecommendations();
          break;
      }
    },
    [experienceFilter, outcomeFilter, patternTypeFilter, fetchExperiences, fetchPatterns, fetchRecommendations]
  );

  const handleProcessWorkflow = async () => {
    if (!workflowForm.workflow_id) return;
    setIsProcessing(true);
    try {
      await processWorkflow({
        workflow_id: workflowForm.workflow_id,
        repository_id: workflowForm.repository_id || undefined,
        title: workflowForm.title || undefined,
        description: workflowForm.description || undefined,
        outcome: workflowForm.outcome || undefined,
        files_changed: workflowForm.files_changed ? workflowForm.files_changed.split(",").map((s) => s.trim()) : undefined,
        technologies: workflowForm.technologies ? workflowForm.technologies.split(",").map((s) => s.trim()) : undefined,
      });
      setShowWorkflowModal(false);
      setWorkflowForm({ workflow_id: "", repository_id: "", title: "", description: "", outcome: "success", files_changed: "", technologies: "" });
      fetchStats();
      fetchGrowth();
      setActiveTab("experiences");
      fetchExperiences({ limit: 50 });
    } catch {
      // error handled by store
    } finally {
      setIsProcessing(false);
    }
  };

  const handleSubmitFeedback = async () => {
    if (!feedbackForm) return;
    await submitFeedback({
      experience_id: feedbackForm.experienceId,
      feedback_type: feedbackForm.feedbackType as FeedbackType,
      comment: feedbackForm.comment || undefined,
    });
    setFeedbackForm(null);
    fetchExperiences({ limit: 50 });
  };

  const filteredExperiences = experiences.filter((exp) => {
    if (experienceFilter && exp.experience_type !== experienceFilter) return false;
    if (outcomeFilter && exp.outcome !== outcomeFilter) return false;
    return true;
  });

  const filteredPatterns = patterns.filter((p) => {
    if (patternTypeFilter && p.pattern_type !== patternTypeFilter) return false;
    if (patternSearch) {
      const search = patternSearch.toLowerCase();
      return (
        p.name.toLowerCase().includes(search) ||
        p.description.toLowerCase().includes(search) ||
        p.technologies.some((t) => t.toLowerCase().includes(search))
      );
    }
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-text">Learning Center</h1>
          <p className="mt-1 text-sm text-text-muted">
            Engineering knowledge base — experiences, patterns, and lessons learned
          </p>
        </div>
        <Button onClick={() => setShowWorkflowModal(true)} leftIcon={<Workflow className="h-4 w-4" />}>
          Process Workflow
        </Button>
      </div>

      {/* Error display */}
      {error && (
        <div className="flex items-center gap-2 rounded-lg border border-danger/50 bg-danger/10 p-3 text-sm text-danger">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{error}</span>
          <Button variant="ghost" size="sm" onClick={clearError} className="ml-auto">
            Dismiss
          </Button>
        </div>
      )}

      {/* Main Tabs */}
      <Tabs value={activeTab} onValueChange={handleTabChange}>
        <TabsList className="w-full justify-start">
          <TabsTrigger value="overview" className="gap-1.5">
            <BarChart3 className="h-4 w-4" />
            Overview
          </TabsTrigger>
          <TabsTrigger value="experiences" className="gap-1.5">
            <BookOpen className="h-4 w-4" />
            Experiences
          </TabsTrigger>
          <TabsTrigger value="patterns" className="gap-1.5">
            <Lightbulb className="h-4 w-4" />
            Patterns
          </TabsTrigger>
          <TabsTrigger value="lessons" className="gap-1.5">
            <AlertTriangle className="h-4 w-4" />
            Lessons
          </TabsTrigger>
          <TabsTrigger value="recommendations" className="gap-1.5">
            <Target className="h-4 w-4" />
            Recommendations
          </TabsTrigger>
        </TabsList>

        {/* ========== OVERVIEW TAB ========== */}
        <TabsContent value="overview" className="space-y-6">
          {/* Stats Cards */}
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-text-muted">Total Experiences</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-2">
                  <BookOpen className="h-5 w-5 text-accent" />
                  <span className="text-2xl font-bold text-text">{stats?.total_experiences ?? 0}</span>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-text-muted">Patterns</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-2">
                  <Lightbulb className="h-5 w-5 text-yellow-400" />
                  <span className="text-2xl font-bold text-text">{stats?.total_patterns ?? 0}</span>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-text-muted">Lessons</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5 text-orange-400" />
                  <span className="text-2xl font-bold text-text">{stats?.total_lessons ?? 0}</span>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-text-muted">Success Rate</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-2">
                  <TrendingUp className="h-5 w-5 text-green-400" />
                  <span className="text-2xl font-bold text-text">
                    {stats?.success_rate != null ? `${Math.round(stats.success_rate * 100)}%` : "—"}
                  </span>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-text-muted">Tasks Processed</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-2">
                  <Brain className="h-5 w-5 text-purple-400" />
                  <span className="text-2xl font-bold text-text">{stats?.total_tasks ?? 0}</span>
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            {/* Growth Timeline */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-text">
                  <TrendingUp className="h-5 w-5 text-accent" />
                  Knowledge Growth
                </CardTitle>
                <CardDescription>Cumulative learning over time</CardDescription>
              </CardHeader>
              <CardContent>
                {growth && growth.timeline.length > 0 ? (
                  <div className="space-y-3">
                    {growth.timeline.slice(-7).map((entry, idx) => {
                      const maxVal = Math.max(
                        ...growth.timeline.map((e) => e.experiences + e.patterns + e.lessons),
                        1
                      );
                      const total = entry.experiences + entry.patterns + entry.lessons;
                      const widthPct = (total / maxVal) * 100;
                      return (
                        <div key={idx} className="space-y-1">
                          <div className="flex items-center justify-between text-xs text-text-muted">
                            <span>{formatDate(entry.date)}</span>
                            <span className="font-medium text-text">{total} items</span>
                          </div>
                          <div className="flex h-2 w-full overflow-hidden rounded-full bg-surface-hover">
                            <div
                              className="bg-accent transition-all"
                              style={{ width: `${(entry.experiences / Math.max(total, 1)) * widthPct}%` }}
                            />
                            <div
                              className="bg-yellow-400 transition-all"
                              style={{ width: `${(entry.patterns / Math.max(total, 1)) * widthPct}%` }}
                            />
                            <div
                              className="bg-orange-400 transition-all"
                              style={{ width: `${(entry.lessons / Math.max(total, 1)) * widthPct}%` }}
                            />
                          </div>
                        </div>
                      );
                    })}
                    <div className="flex items-center gap-4 pt-2 text-xs text-text-muted">
                      <span className="flex items-center gap-1"><span className="inline-block h-2 w-2 rounded-full bg-accent" />Experiences</span>
                      <span className="flex items-center gap-1"><span className="inline-block h-2 w-2 rounded-full bg-yellow-400" />Patterns</span>
                      <span className="flex items-center gap-1"><span className="inline-block h-2 w-2 rounded-full bg-orange-400" />Lessons</span>
                    </div>
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center py-8 text-text-muted">
                    <BarChart3 className="mb-2 h-8 w-8" />
                    <p className="text-sm">No growth data yet</p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Recent Activity */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-text">
                  <Clock className="h-5 w-5 text-accent" />
                  Recent Activity
                </CardTitle>
                <CardDescription>Latest learning tasks processed</CardDescription>
              </CardHeader>
              <CardContent>
                {tasks.length > 0 ? (
                  <div className="space-y-3">
                    {tasks.slice(0, 8).map((task) => (
                      <div
                        key={task.task_id}
                        className="flex items-center justify-between rounded-lg border border-border p-3 transition-colors hover:bg-surface-hover"
                      >
                        <div className="flex items-center gap-3">
                          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-accent/20">
                            <Brain className="h-4 w-4 text-accent" />
                          </div>
                          <div>
                            <p className="text-sm font-medium text-text">
                              Task {task.task_id.slice(0, 8)}
                            </p>
                            <p className="text-xs text-text-muted">
                              {task.experiences_count} exp · {task.patterns_count} patterns · {task.lessons_count} lessons
                            </p>
                          </div>
                        </div>
                        <div className="text-right">
                          <Badge variant={task.status === "completed" ? "success" : task.status === "failed" ? "destructive" : "secondary"}>
                            {task.status}
                          </Badge>
                          <p className="mt-1 text-xs text-text-muted">
                            {formatRelativeTime(task.started_at)}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center py-8 text-text-muted">
                    <Clock className="mb-2 h-8 w-8" />
                    <p className="text-sm">No tasks processed yet</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* ========== EXPERIENCES TAB ========== */}
        <TabsContent value="experiences" className="space-y-4">
          {/* Filters */}
          <Card>
            <CardContent className="flex flex-wrap items-center gap-3 pt-6">
              <div className="flex items-center gap-2">
                <Filter className="h-4 w-4 text-text-muted" />
                <span className="text-sm font-medium text-text">Filters:</span>
              </div>
              <select
                value={experienceFilter}
                onChange={(e) => setExperienceFilter(e.target.value as ExperienceType | "")}
                className="rounded-md border border-border bg-surface px-3 py-1.5 text-sm text-text focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
              >
                <option value="">All Types</option>
                {Object.entries(EXPERIENCE_TYPE_CONFIG).map(([key, cfg]) => (
                  <option key={key} value={key}>{cfg.label}</option>
                ))}
              </select>
              <select
                value={outcomeFilter}
                onChange={(e) => setOutcomeFilter(e.target.value as OutcomeType | "")}
                className="rounded-md border border-border bg-surface px-3 py-1.5 text-sm text-text focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
              >
                <option value="">All Outcomes</option>
                <option value="success">Success</option>
                <option value="failure">Failure</option>
                <option value="partial">Partial</option>
              </select>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  fetchExperiences({
                    experience_type: experienceFilter || undefined,
                    outcome: outcomeFilter || undefined,
                    limit: 50,
                  });
                }}
                leftIcon={<RefreshCw className="h-3.5 w-3.5" />}
              >
                Refresh
              </Button>
            </CardContent>
          </Card>

          {/* Experience List */}
          {filteredExperiences.length > 0 ? (
            <div className="space-y-3">
              {filteredExperiences.map((exp, idx) => {
                const typeConfig = EXPERIENCE_TYPE_CONFIG[exp.experience_type] || {
                  label: exp.experience_type,
                  icon: <Code className="h-3.5 w-3.5" />,
                  color: "bg-gray-500/20 text-gray-400",
                };
                const files = exp.files_changed || [];
                const solution = exp.solution || "";
                return (
                  <Card key={`${exp.id}-${idx}`} className="transition-shadow hover:shadow-md">
                    <CardContent className="pt-6">
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1 space-y-2">
                          <div className="flex items-center gap-2">
                            <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${typeConfig.color}`}>
                              {typeConfig.icon}
                              {typeConfig.label}
                            </span>
                            {getOutcomeBadge(exp.outcome)}
                            {exp.workflow_id && (
                              <Badge variant="outline" className="text-xs">Workflow: {exp.workflow_id.slice(0, 8)}</Badge>
                            )}
                          </div>
                          <h3 className="text-sm font-semibold text-text">{exp.title}</h3>
                          <p className="text-xs text-text-muted line-clamp-2">{exp.description}</p>

                          {/* Files changed */}
                          {files.length > 0 && (
                            <div className="flex flex-wrap gap-1">
                              {files.slice(0, 5).map((f: string) => (
                                <Badge key={f} variant="outline" className="text-xs font-mono">{f.split("/").pop()}</Badge>
                              ))}
                              {files.length > 5 && <Badge variant="outline" className="text-xs">+{files.length - 5}</Badge>}
                            </div>
                          )}

                          {/* Solution preview */}
                          {solution && (
                            <div className="rounded-md bg-surface-hover p-2">
                              <p className="text-xs text-text-muted line-clamp-2">{solution}</p>
                            </div>
                          )}

                          <div className="flex flex-wrap items-center gap-2">
                            {exp.technologies.slice(0, 5).map((tech) => (
                              <Badge key={tech} variant="outline" className="text-xs">
                                {tech}
                              </Badge>
                            ))}
                          </div>
                        </div>
                        <div className="flex flex-col items-end gap-2">
                          <div className="text-right">
                            <p className="text-xs text-text-muted">Confidence</p>
                            <p className={`text-sm font-bold ${getConfidenceColor(exp.confidence)}`}>
                              {Math.round(exp.confidence * 100)}%
                            </p>
                          </div>
                          <div className="text-right">
                            <p className="text-xs text-text-muted">Reuse</p>
                            <p className={`text-sm font-bold ${getConfidenceColor(exp.reuse_potential)}`}>
                              {Math.round(exp.reuse_potential * 100)}%
                            </p>
                          </div>
                          <p className="text-xs text-text-muted">{formatDate(exp.created_at)}</p>
                        </div>
                      </div>
                      {/* Feedback Buttons */}
                      <div className="mt-3 flex items-center gap-2 border-t border-border pt-3">
                        <span className="text-xs text-text-muted">Feedback:</span>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() =>
                            setFeedbackForm({
                              experienceId: exp.id,
                              feedbackType: "helpful",
                              comment: "",
                            })
                          }
                          className="h-7 gap-1 text-xs"
                        >
                          <ThumbsUp className="h-3 w-3" /> Helpful
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() =>
                            setFeedbackForm({
                              experienceId: exp.id,
                              feedbackType: "excellent",
                              comment: "",
                            })
                          }
                          className="h-7 gap-1 text-xs"
                        >
                          <Sparkles className="h-3 w-3" /> Excellent
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() =>
                            setFeedbackForm({
                              experienceId: exp.id,
                              feedbackType: "needs_improvement",
                              comment: "",
                            })
                          }
                          className="h-7 gap-1 text-xs"
                        >
                          <ArrowUpRight className="h-3 w-3" /> Improve
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          ) : (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12 text-text-muted">
                <BookOpen className="mb-3 h-10 w-10" />
                <p className="text-sm font-medium">No experiences found</p>
                <p className="text-xs">Process a workflow to start collecting experiences</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* ========== PATTERNS TAB ========== */}
        <TabsContent value="patterns" className="space-y-4">
          {/* Search and Filters */}
          <Card>
            <CardContent className="flex flex-wrap items-center gap-3 pt-6">
              <div className="relative flex-1 min-w-[200px]">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-muted" />
                <Input
                  placeholder="Search patterns by name, description, or technology..."
                  value={patternSearch}
                  onChange={(e) => setPatternSearch(e.target.value)}
                  className="pl-9"
                />
              </div>
              <select
                value={patternTypeFilter}
                onChange={(e) => setPatternTypeFilter(e.target.value as PatternType | "")}
                className="rounded-md border border-border bg-surface px-3 py-1.5 text-sm text-text focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
              >
                <option value="">All Types</option>
                {Object.entries(PATTERN_TYPE_CONFIG).map(([key, cfg]) => (
                  <option key={key} value={key}>{cfg.label}</option>
                ))}
              </select>
              <Button
                variant="ghost"
                size="sm"
                onClick={() =>
                  fetchPatterns({
                    pattern_type: patternTypeFilter || undefined,
                    limit: 50,
                  })
                }
                leftIcon={<RefreshCw className="h-3.5 w-3.5" />}
              >
                Refresh
              </Button>
            </CardContent>
          </Card>

          {/* Pattern Cards */}
          {filteredPatterns.length > 0 ? (
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              {filteredPatterns.map((pattern) => {
                const typeConfig = PATTERN_TYPE_CONFIG[pattern.pattern_type] || {
                  label: pattern.pattern_type,
                  icon: <Lightbulb className="h-3.5 w-3.5" />,
                };
                return (
                  <Card key={pattern.id} className="transition-shadow hover:shadow-md">
                    <CardHeader>
                      <div className="flex items-start justify-between">
                        <div className="flex items-center gap-2">
                          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent/20">
                            {typeConfig.icon}
                          </div>
                          <div>
                            <CardTitle className="text-sm text-text">{pattern.name}</CardTitle>
                            <CardDescription className="text-xs">
                              {typeConfig.label} · Used {pattern.usage_count} times
                            </CardDescription>
                          </div>
                        </div>
                        <Badge variant={getConfidenceVariant(pattern.confidence)}>
                          {Math.round(pattern.confidence * 100)}%
                        </Badge>
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      <p className="text-xs text-text-muted line-clamp-2">{pattern.description}</p>

                      {pattern.code_example && (
                        <div className="rounded-md bg-surface-hover p-3">
                          <pre className="overflow-x-auto text-xs text-text">
                            <code>{pattern.code_example.slice(0, 200)}{pattern.code_example.length > 200 ? "..." : ""}</code>
                          </pre>
                        </div>
                      )}

                      <div className="space-y-2 text-xs">
                        <div className="flex items-start gap-2">
                          <CheckCircle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-green-400" />
                          <span className="text-text-muted">
                            <span className="font-medium text-text">When to use:</span> {pattern.when_to_use}
                          </span>
                        </div>
                        {pattern.when_not_to_use && (
                          <div className="flex items-start gap-2">
                            <XCircle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-red-400" />
                            <span className="text-text-muted">
                              <span className="font-medium text-text">Avoid when:</span> {pattern.when_not_to_use}
                            </span>
                          </div>
                        )}
                      </div>

                      <div className="flex flex-wrap gap-1.5">
                        {pattern.technologies.slice(0, 3).map((tech) => (
                          <Badge key={tech} variant="outline" className="text-xs">{tech}</Badge>
                        ))}
                      </div>

                      <div className="flex items-center justify-between border-t border-border pt-2 text-xs text-text-muted">
                        <span>Success: {Math.round(pattern.success_rate * 100)}%</span>
                        <span>Generalization: {Math.round(pattern.generalization_score * 100)}%</span>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          ) : (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12 text-text-muted">
                <Lightbulb className="mb-3 h-10 w-10" />
                <p className="text-sm font-medium">No patterns found</p>
                <p className="text-xs">Patterns are extracted from successful experiences</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* ========== LESSONS TAB ========== */}
        <TabsContent value="lessons" className="space-y-4">
          {lessons.length > 0 ? (
            <div className="space-y-3">
              {lessons.map((lesson) => {
                const typeConfig = LESSON_TYPE_CONFIG[lesson.lesson_type] || {
                  label: lesson.lesson_type,
                  icon: <AlertTriangle className="h-3.5 w-3.5" />,
                };
                const sevConfig = SEVERITY_CONFIG[lesson.severity] || {
                  label: lesson.severity,
                  variant: "secondary" as const,
                };
                return (
                  <Card key={lesson.id} className="transition-shadow hover:shadow-md">
                    <CardContent className="pt-6">
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1 space-y-2">
                          <div className="flex items-center gap-2">
                            <span className="inline-flex items-center gap-1 text-xs text-text-muted">
                              {typeConfig.icon}
                              {typeConfig.label}
                            </span>
                            <Badge variant={sevConfig.variant}>{sevConfig.label}</Badge>
                            <Badge variant={getConfidenceVariant(lesson.confidence)}>
                              {Math.round(lesson.confidence * 100)}% confidence
                            </Badge>
                          </div>
                          <h3 className="text-sm font-semibold text-text">{lesson.title}</h3>
                          <p className="text-xs text-text-muted">{lesson.description}</p>

                          <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                            <div className="rounded-md border border-danger/30 bg-danger/5 p-3">
                              <p className="mb-1 text-xs font-medium text-danger">Root Cause</p>
                              <p className="text-xs text-text-muted">{lesson.root_cause}</p>
                            </div>
                            <div className="rounded-md border border-success/30 bg-success/5 p-3">
                              <p className="mb-1 text-xs font-medium text-success">How to Avoid</p>
                              <p className="text-xs text-text-muted">{lesson.avoidance_strategy}</p>
                            </div>
                          </div>

                          <div className="flex flex-wrap gap-1.5">
                            {lesson.technologies.map((tech) => (
                              <Badge key={tech} variant="outline" className="text-xs">{tech}</Badge>
                            ))}
                          </div>
                        </div>

                        <div className="flex flex-col items-end gap-2">
                          <div className="rounded-lg bg-surface-hover px-3 py-2 text-center">
                            <p className="text-lg font-bold text-text">{lesson.times_encountered}</p>
                            <p className="text-xs text-text-muted">encounters</p>
                          </div>
                          <p className="text-xs text-text-muted">{formatDate(lesson.created_at)}</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          ) : (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12 text-text-muted">
                <AlertTriangle className="mb-3 h-10 w-10" />
                <p className="text-sm font-medium">No lessons recorded</p>
                <p className="text-xs">Lessons are captured from failures and issues</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* ========== RECOMMENDATIONS TAB ========== */}
        <TabsContent value="recommendations" className="space-y-4">
          {recommendations.length > 0 ? (
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              {recommendations.filter((rec) => {
                // Skip old-format generic recs
                const recType = rec.recommendation_type || "";
                const source = rec.source_name || "";
                const desc = rec.description || "";
                const title = (rec.title || rec.task_type || "").toLowerCase();
                const recText = rec.recommendation || "";

                // Old format: no recommendation_type, no source, empty description
                if (!recType && !source && !desc && ["approach", "architecture", "security", "testing", "general"].includes(title)) return false;
                // Old template text
                if (!recType && !source && (recText.includes("Proven Pattern:") || recText.includes("Recommended Approach") || recText.includes("Architecture Recommendation") || recText.includes("Security Guidance") || recText.includes("Testing Strategy"))) return false;
                // Empty rec
                if (!desc && !source && !rec.title) return false;
                return true;
              }).map((rec) => {
                const priConfig = PRIORITY_CONFIG[rec.priority] || { label: rec.priority || "Medium", variant: "secondary" as const };
                const recType = rec.recommendation_type || "general";
                const typeColors: Record<string, string> = {
                  pattern: "bg-blue-500/20 text-blue-400",
                  proven: "bg-green-500/20 text-green-400",
                  avoidance: "bg-red-500/20 text-red-400",
                  lesson: "bg-orange-500/20 text-orange-400",
                  technology: "bg-purple-500/20 text-purple-400",
                  "task-guidance": "bg-cyan-500/20 text-cyan-400",
                  risk: "bg-yellow-500/20 text-yellow-400",
                };
                const typeLabels: Record<string, string> = {
                  pattern: "Pattern",
                  proven: "Proven",
                  avoidance: "Avoid",
                  lesson: "Lesson",
                  technology: "Tech",
                  "task-guidance": "Guidance",
                  risk: "Risk",
                };
                return (
                  <Card key={rec.id} className="transition-shadow hover:shadow-md">
                    <CardHeader>
                      <div className="flex items-start justify-between">
                        <div className="flex items-center gap-2">
                          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent/20">
                            <Target className="h-4 w-4 text-accent" />
                          </div>
                          <div>
                            <CardTitle className="text-sm text-text">{rec.title || rec.task_type || "Recommendation"}</CardTitle>
                            <CardDescription className="text-xs">
                              {rec.source_name ? `Source: ${rec.source_name}` : priConfig.label}
                            </CardDescription>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${typeColors[recType] || "bg-gray-500/20 text-gray-400"}`}>
                            {typeLabels[recType] || recType}
                          </span>
                          <Badge variant={priConfig.variant}>{priConfig.label}</Badge>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      <p className="text-xs text-text-muted whitespace-pre-line">{rec.description || rec.recommendation}</p>

                      {(rec.context_keywords || []).length > 0 && (
                        <div className="flex flex-wrap gap-1.5">
                          {(rec.context_keywords || []).slice(0, 5).map((kw: string) => (
                            <Badge key={kw} variant="outline" className="text-xs">{kw}</Badge>
                          ))}
                        </div>
                      )}

                      <div className="flex flex-wrap gap-1.5">
                        {(rec.technologies || []).map((tech: string) => (
                          <Badge key={tech} variant="secondary" className="text-xs">{tech}</Badge>
                        ))}
                      </div>

                      <div className="flex items-center justify-between border-t border-border pt-2">
                        <span className={`text-xs font-medium ${getConfidenceColor(rec.confidence)}`}>
                          Confidence: {Math.round(rec.confidence * 100)}%
                        </span>
                        <span className="text-xs text-text-muted">{formatDate(rec.created_at)}</span>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          ) : (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12 text-text-muted">
                <Target className="mb-3 h-10 w-10" />
                <p className="text-sm font-medium">No recommendations yet</p>
                <p className="text-xs">Process a workflow to generate recommendations</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>

      {/* Process Workflow Modal */}
      <Modal open={showWorkflowModal} onOpenChange={setShowWorkflowModal}>
        <ModalContent>
          <ModalHeader>
            <ModalTitle>Process Workflow for Learning</ModalTitle>
            <ModalDescription>
              Submit workflow data to extract experiences, patterns, and lessons.
            </ModalDescription>
          </ModalHeader>
          <div className="space-y-4">
            <div>
              <label className="mb-2 block text-sm font-medium text-text">Project *</label>
              <select
                value={workflowForm.workflow_id}
                onChange={(e) => {
                  const project = projects.find((p) => p.id === e.target.value);
                  if (project) {
                    const techs = [...(project.frameworks || []), ...(project.languages || [])];
                    setWorkflowForm((prev) => ({
                      ...prev,
                      workflow_id: project.id,
                      title: project.name,
                      description: project.description || "",
                      technologies: techs.join(", "),
                    }));
                  } else {
                    setWorkflowForm((prev) => ({
                      ...prev,
                      workflow_id: "",
                      title: "",
                      description: "",
                      technologies: "",
                    }));
                  }
                }}
                className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-text focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
              >
                <option value="">Select a project...</option>
                {projects.map((p) => (
                  <option key={p.id} value={p.id}>{p.name}</option>
                ))}
              </select>
            </div>
            <Input
              label="Title"
              placeholder="Brief title for this workflow"
              value={workflowForm.title}
              onChange={(e) => setWorkflowForm((prev) => ({ ...prev, title: e.target.value }))}
            />
            <Textarea
              label="Description"
              placeholder="What was accomplished in this workflow..."
              value={workflowForm.description}
              onChange={(e) => setWorkflowForm((prev) => ({ ...prev, description: e.target.value }))}
              rows={3}
            />
            <div>
              <label className="mb-2 block text-sm font-medium text-text">Outcome</label>
              <select
                value={workflowForm.outcome}
                onChange={(e) => setWorkflowForm((prev) => ({ ...prev, outcome: e.target.value }))}
                className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-text focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
              >
                <option value="success">Success</option>
                <option value="failure">Failure</option>
                <option value="partial">Partial</option>
              </select>
            </div>
            <Input
              label="Files Changed"
              placeholder="Comma-separated file paths"
              value={workflowForm.files_changed}
              onChange={(e) => setWorkflowForm((prev) => ({ ...prev, files_changed: e.target.value }))}
            />
            <Input
              label="Technologies"
              placeholder="Comma-separated technologies used"
              value={workflowForm.technologies}
              onChange={(e) => setWorkflowForm((prev) => ({ ...prev, technologies: e.target.value }))}
            />
          </div>
          <ModalFooter>
            <Button variant="outline" onClick={() => setShowWorkflowModal(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleProcessWorkflow}
              isLoading={isProcessing}
              disabled={!workflowForm.workflow_id}
            >
              <Brain className="mr-2 h-4 w-4" />
              Process
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>

      {/* Feedback Modal */}
      <Modal open={!!feedbackForm} onOpenChange={() => setFeedbackForm(null)}>
        <ModalContent>
          <ModalHeader>
            <ModalTitle>Submit Feedback</ModalTitle>
            <ModalDescription>
              Help improve this experience with your feedback.
            </ModalDescription>
          </ModalHeader>
          <div className="space-y-4">
            <div>
              <label className="mb-2 block text-sm font-medium text-text">Feedback Type</label>
              <select
                value={feedbackForm?.feedbackType || ""}
                onChange={(e) =>
                  setFeedbackForm((prev) =>
                    prev ? { ...prev, feedbackType: e.target.value } : null
                  )
                }
                className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-text focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
              >
                <option value="helpful">Helpful</option>
                <option value="excellent">Excellent</option>
                <option value="needs_improvement">Needs Improvement</option>
                <option value="incorrect">Incorrect</option>
              </select>
            </div>
            <Textarea
              label="Comments (optional)"
              placeholder="Any additional notes..."
              value={feedbackForm?.comment || ""}
              onChange={(e) =>
                setFeedbackForm((prev) =>
                  prev ? { ...prev, comment: e.target.value } : null
                )
              }
              rows={3}
            />
          </div>
          <ModalFooter>
            <Button variant="outline" onClick={() => setFeedbackForm(null)}>
              Cancel
            </Button>
            <Button onClick={handleSubmitFeedback} isLoading={isLoading}>
              Submit Feedback
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </div>
  );
}
