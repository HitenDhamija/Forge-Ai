"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Code2,
  FileCode,
  CheckCircle,
  XCircle,
  Clock,
  Loader2,
  Play,
  Wrench,
  AlertTriangle,
  FolderKanban,
  History,
  Eye,
} from "lucide-react";
import { apiClient } from "@/services/api";
import { useProjectStore } from "@/stores/project-store";

interface Task {
  task_id: string;
  repository_id: string;
  task_description: string;
  task_type: string;
  state: string;
  target_files: string[];
  generated_code?: Array<{ file_path: string; content: string; explanation: string }>;
  diffs?: Array<{ file_path: string; stats: { additions: number; deletions: number }; is_new_file: boolean }>;
  review_result?: { passed: boolean; score: number; summary: string };
  validation_result?: { valid: boolean; errors: string[]; warnings: string[] };
  commit_summary?: { message: string; description: string; files_changed: string[] };
  guidance_response?: {
    suggestions: Array<{
      title: string;
      description: string;
      priority: string;
      estimated_effort: string;
      files_affected: string[];
      task_type?: string;
      task_description?: string;
    }>;
    recommendations: string[];
    next_steps: string[];
    analysis_summary: string;
    project_health: {
      test_coverage: string;
      documentation: string;
      code_quality: string;
      tech_stack?: string;
      file_count?: number;
      gaps_found?: number;
    };
  };
  error?: string;
  execution_log: Array<{ timestamp: string; state: string; message: string }>;
  started_at: string;
  completed_at?: string;
}

const TASK_TYPES = [
  { value: "feature", label: "Feature Implementation" },
  { value: "bug_fix", label: "Bug Fix" },
  { value: "refactor", label: "Refactoring" },
  { value: "api_creation", label: "API Creation" },
  { value: "database_migration", label: "Database Migration" },
  { value: "frontend_component", label: "Frontend Component" },
  { value: "backend_service", label: "Backend Service" },
  { value: "documentation", label: "Documentation" },
  { value: "guidance", label: "Guidance & Suggestions" },
];

const STATE_COLORS: Record<string, string> = {
  idle: "bg-gray-500",
  analyzing: "bg-blue-500",
  planning: "bg-yellow-500",
  generating: "bg-purple-500",
  reviewing: "bg-orange-500",
  validating: "bg-cyan-500",
  awaiting_approval: "bg-amber-500",
  completed: "bg-green-500",
  failed: "bg-red-500",
};

export function SoftwareEngineerWorkspace() {
  const { projects } = useProjectStore();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [selectedRepoId, setSelectedRepoId] = useState("");
  const [taskDescription, setTaskDescription] = useState("");
  const [taskType, setTaskType] = useState("feature");
  const [targetFiles, setTargetFiles] = useState("");
  const [isExecuting, setIsExecuting] = useState(false);
  const [showApprovalDialog, setShowApprovalDialog] = useState(false);
  const [showCodeDialog, setShowCodeDialog] = useState(false);
  const [activeTab, setActiveTab] = useState("overview");

  useEffect(() => {
    fetchTasks();
    if (projects.length > 0 && !selectedRepoId) {
      setSelectedRepoId(projects[0].id);
    }
  }, [projects]);

  const fetchTasks = async () => {
    try {
      const response = await apiClient.get("/software-engineer/history");
      const data = response.data?.data ?? response.data;
      setTasks(data?.tasks || []);
    } catch (error) {
      console.error("Failed to fetch tasks:", error);
    }
  };

  const executeTask = async () => {
    if (!selectedRepoId || !taskDescription.trim()) return;
    setIsExecuting(true);
    try {
      const response = await apiClient.post("/software-engineer/execute", {
        repository_id: selectedRepoId,
        task_description: taskDescription,
        task_type: taskType,
        target_files: targetFiles.split("\n").filter(Boolean),
      });
      const task = response.data?.data ?? response.data;
      setTasks([task, ...tasks]);
      setSelectedTask(task);
      setTaskDescription("");
      setTargetFiles("");
    } catch (error) {
      console.error("Failed to execute task:", error);
    } finally {
      setIsExecuting(false);
    }
  };

  const approveTask = async () => {
    if (!selectedTask) return;
    try {
      const response = await apiClient.post("/software-engineer/approve", {
        task_id: selectedTask.task_id,
      });
      const updated = response.data?.data ?? response.data;
      setTasks(tasks.map((t) => (t.task_id === updated.task_id ? updated : t)));
      setSelectedTask(updated);
      setShowApprovalDialog(false);
    } catch (error) {
      console.error("Failed to approve:", error);
    }
  };

  const rejectTask = async (reason: string) => {
    if (!selectedTask) return;
    try {
      const response = await apiClient.post("/software-engineer/reject", {
        task_id: selectedTask.task_id,
        reason,
      });
      const updated = response.data?.data ?? response.data;
      setTasks(tasks.map((t) => (t.task_id === updated.task_id ? updated : t)));
      setSelectedTask(updated);
      setShowApprovalDialog(false);
    } catch (error) {
      console.error("Failed to reject:", error);
    }
  };

  const getStateIcon = (state: string) => {
    switch (state) {
      case "completed": return <CheckCircle className="h-4 w-4 text-green-500" />;
      case "failed": return <XCircle className="h-4 w-4 text-red-500" />;
      case "awaiting_approval": return <AlertTriangle className="h-4 w-4 text-amber-500" />;
      default: return <Clock className="h-4 w-4 text-blue-500" />;
    }
  };

  const selectedProject = projects.find((p) => p.id === selectedRepoId);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Software Engineer</h1>
          <p className="text-muted-foreground">
            AI-powered code implementation — describe a task, select a project, and execute
          </p>
        </div>
        <Button onClick={fetchTasks} variant="outline">
          <History className="mr-2 h-4 w-4" /> Refresh
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Task Input Panel */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle>New Task</CardTitle>
            <CardDescription>Select a project and describe the task</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-1 block">Project</label>
              {projects.length > 0 ? (
                <Select value={selectedRepoId} onValueChange={setSelectedRepoId}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select a project" />
                  </SelectTrigger>
                  <SelectContent>
                    {projects.map((p) => (
                      <SelectItem key={p.id} value={p.id}>
                        <div className="flex items-center gap-2">
                          <FolderKanban className="h-4 w-4" />
                          {p.name}
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              ) : (
                <p className="text-sm text-muted-foreground">
                  No projects yet. Import a repository first.
                </p>
              )}
            </div>

            {selectedProject && (
              <div className="p-3 rounded-lg bg-surface text-sm">
                <p className="font-medium">{selectedProject.name}</p>
                {Array.isArray(selectedProject.languages) && selectedProject.languages.length > 0 && (
                  <p className="text-text-muted text-xs mt-1">
                    {selectedProject.languages.map((l: any) => l.name || l).join(", ")}
                  </p>
                )}
              </div>
            )}

            <div>
              <label className="text-sm font-medium mb-1 block">Task Type</label>
              <Select value={taskType} onValueChange={setTaskType}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {TASK_TYPES.map((type) => (
                    <SelectItem key={type.value} value={type.value}>
                      {type.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="text-sm font-medium mb-1 block">Task Description</label>
              <Textarea
                placeholder="e.g., Add input validation to the user registration endpoint..."
                value={taskDescription}
                onChange={(e) => setTaskDescription(e.target.value)}
                rows={4}
              />
            </div>

            <div>
              <label className="text-sm font-medium mb-1 block">Target Files (optional, one per line)</label>
              <Textarea
                placeholder={"src/services/auth.py\nsrc/api/auth.py"}
                value={targetFiles}
                onChange={(e) => setTargetFiles(e.target.value)}
                rows={3}
              />
            </div>

            <Button
              onClick={executeTask}
              disabled={!selectedRepoId || !taskDescription.trim() || isExecuting}
              className="w-full"
            >
              {isExecuting ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Play className="mr-2 h-4 w-4" />
              )}
              Execute Task
            </Button>
          </CardContent>
        </Card>

        {/* Main Content Area */}
        <div className="lg:col-span-2 space-y-6">
          {selectedTask ? (
            <>
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      {getStateIcon(selectedTask.state)}
                      <div>
                        <CardTitle className="text-lg">{selectedTask.task_description}</CardTitle>
                        <CardDescription>
                          {TASK_TYPES.find((t) => t.value === selectedTask.task_type)?.label || selectedTask.task_type}
                          {" • "}
                          {projects.find((p) => p.id === selectedTask.repository_id)?.name || selectedTask.repository_id}
                        </CardDescription>
                      </div>
                    </div>
                    <Badge className={STATE_COLORS[selectedTask.state]}>
                      {selectedTask.state.replace("_", " ")}
                    </Badge>
                  </div>
                </CardHeader>
              </Card>

              <Card>
                <CardContent className="pt-6">
                  <Tabs value={activeTab} onValueChange={setActiveTab}>
                    <TabsList>
                      <TabsTrigger value="overview">Overview</TabsTrigger>
                      <TabsTrigger value="code">Generated Code</TabsTrigger>
                      <TabsTrigger value="diff">Diff</TabsTrigger>
                      <TabsTrigger value="review">Review</TabsTrigger>
                      <TabsTrigger value="guidance">Guidance</TabsTrigger>
                      <TabsTrigger value="log">Execution Log</TabsTrigger>
                    </TabsList>

                    <TabsContent value="overview" className="space-y-4">
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <h4 className="font-medium mb-2">Target Files</h4>
                          <div className="space-y-1">
                            {(selectedTask.target_files?.length ? selectedTask.target_files : ["(auto-detected)"]).map((file) => (
                              <div key={file} className="flex items-center gap-2 text-sm">
                                <FileCode className="h-4 w-4" />
                                {file}
                              </div>
                            ))}
                          </div>
                        </div>
                        <div>
                          <h4 className="font-medium mb-2">Commit Summary</h4>
                          {selectedTask.commit_summary ? (
                            <div className="text-sm space-y-1">
                              <p className="font-mono bg-muted p-2 rounded text-xs">
                                {selectedTask.commit_summary.message}
                              </p>
                              <p className="text-muted-foreground">
                                {selectedTask.commit_summary.files_changed.length} files changed
                              </p>
                            </div>
                          ) : (
                            <p className="text-sm text-muted-foreground">Pending...</p>
                          )}
                        </div>
                      </div>
                    </TabsContent>

                    <TabsContent value="code" className="space-y-4">
                      {selectedTask.generated_code?.length ? (
                        selectedTask.generated_code.map((code) => (
                          <div key={code.file_path} className="space-y-2">
                            <div className="flex items-center justify-between">
                              <h4 className="font-medium text-sm">{code.file_path}</h4>
                              <Badge variant="outline" className="text-xs">{code.explanation}</Badge>
                            </div>
                            <pre className="bg-muted p-4 rounded-lg overflow-auto max-h-64 text-xs font-mono whitespace-pre-wrap">
                              {code.content}
                            </pre>
                          </div>
                        ))
                      ) : (
                        <p className="text-muted-foreground text-sm">No code generated yet.</p>
                      )}
                    </TabsContent>

                    <TabsContent value="diff" className="space-y-4">
                      {selectedTask.diffs?.length ? (
                        selectedTask.diffs.map((diff) => (
                          <div key={diff.file_path} className="flex items-center justify-between p-3 bg-muted rounded-lg">
                            <div className="flex items-center gap-2">
                              {diff.is_new_file ? (
                                <Badge className="bg-green-500 text-xs">new</Badge>
                              ) : (
                                <Badge variant="outline" className="text-xs">modified</Badge>
                              )}
                              <span className="font-mono text-sm">{diff.file_path}</span>
                            </div>
                            <div className="flex gap-2">
                              <Badge variant="outline" className="text-green-500 text-xs">+{diff.stats.additions}</Badge>
                              <Badge variant="outline" className="text-red-500 text-xs">-{diff.stats.deletions}</Badge>
                            </div>
                          </div>
                        ))
                      ) : (
                        <p className="text-muted-foreground text-sm">No diffs available yet.</p>
                      )}
                    </TabsContent>

                    <TabsContent value="review" className="space-y-4">
                      {selectedTask.review_result ? (
                        <div className="space-y-4">
                          <div className="flex items-center gap-2">
                            {selectedTask.review_result.passed ? (
                              <CheckCircle className="h-5 w-5 text-green-500" />
                            ) : (
                              <XCircle className="h-5 w-5 text-red-500" />
                            )}
                            <span className="font-medium">Score: {selectedTask.review_result.score}/100</span>
                          </div>
                          <p className="text-sm text-muted-foreground">{selectedTask.review_result.summary}</p>
                        </div>
                      ) : (
                        <p className="text-muted-foreground text-sm">Review pending...</p>
                      )}
                      {selectedTask.validation_result && (
                        <div className="space-y-2">
                          <h4 className="font-medium">Validation</h4>
                          {selectedTask.validation_result.errors.map((e, i) => (
                            <div key={i} className="flex items-center gap-2 text-red-500 text-sm">
                              <XCircle className="h-4 w-4" /> {e}
                            </div>
                          ))}
                          {selectedTask.validation_result.warnings.map((w, i) => (
                            <div key={i} className="flex items-center gap-2 text-yellow-500 text-sm">
                              <AlertTriangle className="h-4 w-4" /> {w}
                            </div>
                          ))}
                        </div>
                      )}
                    </TabsContent>

                    <TabsContent value="guidance" className="space-y-6">
                      {selectedTask.guidance_response ? (
                        <div className="space-y-6">
                          <div className="p-4 bg-muted rounded-lg">
                            <p className="text-sm">{selectedTask.guidance_response.analysis_summary}</p>
                          </div>

                          <div>
                            <h4 className="font-medium mb-3">Suggested Features</h4>
                            <p className="text-xs text-muted-foreground mb-3">Click "Implement" to auto-create a task for any suggestion.</p>
                            <div className="space-y-3">
                              {selectedTask.guidance_response.suggestions.map((suggestion: any, i: number) => (
                                <div key={i} className="p-4 border rounded-lg space-y-2 hover:border-accent transition-colors">
                                  <div className="flex items-center justify-between">
                                    <h5 className="font-medium">{suggestion.title}</h5>
                                    <div className="flex gap-2 items-center">
                                      <Badge variant={suggestion.priority === "high" ? "default" : suggestion.priority === "medium" ? "secondary" : "outline"}>
                                        {suggestion.priority}
                                      </Badge>
                                      <Badge variant="outline">{suggestion.estimated_effort}</Badge>
                                      <Button
                                        size="sm"
                                        variant="outline"
                                        className="ml-2"
                                        onClick={() => {
                                          setTaskDescription(suggestion.task_description || suggestion.description);
                                          setTaskType(suggestion.task_type || "feature");
                                          setTargetFiles((suggestion.files_affected || []).join("\n"));
                                          setActiveTab("overview");
                                        }}
                                      >
                                        <Play className="h-3 w-3 mr-1" /> Implement
                                      </Button>
                                    </div>
                                  </div>
                                  <p className="text-sm text-muted-foreground">{suggestion.description}</p>
                                  {suggestion.files_affected && suggestion.files_affected.length > 0 && (
                                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                                      <FileCode className="h-3 w-3" />
                                      {suggestion.files_affected.join(", ")}
                                    </div>
                                  )}
                                </div>
                              ))}
                            </div>
                          </div>

                          <div className="grid grid-cols-2 gap-4">
                            <div>
                              <h4 className="font-medium mb-2">Recommendations</h4>
                              <ul className="space-y-1">
                                {selectedTask.guidance_response.recommendations.map((rec: string, i: number) => (
                                  <li key={i} className="text-sm flex items-start gap-2">
                                    <CheckCircle className="h-4 w-4 text-green-500 mt-0.5 shrink-0" />
                                    {rec}
                                  </li>
                                ))}
                              </ul>
                            </div>
                            <div>
                              <h4 className="font-medium mb-2">Next Steps</h4>
                              <ul className="space-y-1">
                                {selectedTask.guidance_response.next_steps.map((step: string, i: number) => (
                                  <li key={i} className="text-sm flex items-start gap-2">
                                    <span className="text-muted-foreground">{i + 1}.</span>
                                    {step}
                                  </li>
                                ))}
                              </ul>
                            </div>
                          </div>

                          <div>
                            <h4 className="font-medium mb-2">Project Health</h4>
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                              <div className="p-3 bg-muted rounded-lg text-center">
                                <p className="text-xs text-muted-foreground">Tech Stack</p>
                                <p className="text-sm font-medium">{selectedTask.guidance_response.project_health.tech_stack || "N/A"}</p>
                              </div>
                              <div className="p-3 bg-muted rounded-lg text-center">
                                <p className="text-xs text-muted-foreground">Test Coverage</p>
                                <p className="text-sm font-medium">{selectedTask.guidance_response.project_health.test_coverage}</p>
                              </div>
                              <div className="p-3 bg-muted rounded-lg text-center">
                                <p className="text-xs text-muted-foreground">Documentation</p>
                                <p className="text-sm font-medium">{selectedTask.guidance_response.project_health.documentation}</p>
                              </div>
                              <div className="p-3 bg-muted rounded-lg text-center">
                                <p className="text-xs text-muted-foreground">Gaps Found</p>
                                <p className="text-sm font-medium">{selectedTask.guidance_response.project_health.gaps_found || 0}</p>
                              </div>
                            </div>
                          </div>
                        </div>
                      ) : (
                        <p className="text-muted-foreground text-sm">No guidance available yet.</p>
                      )}
                    </TabsContent>

                    <TabsContent value="log" className="space-y-2">
                      {selectedTask.execution_log.map((log, i) => (
                        <div key={i} className="flex items-start gap-3 text-sm p-2">
                          <span className="text-muted-foreground whitespace-nowrap text-xs">
                            {new Date(log.timestamp).toLocaleTimeString()}
                          </span>
                          <Badge variant="outline" className="text-xs shrink-0">{log.state}</Badge>
                          <span>{log.message}</span>
                        </div>
                      ))}
                    </TabsContent>
                  </Tabs>
                </CardContent>
              </Card>

              {selectedTask.state === "awaiting_approval" && (
                <div className="flex gap-4">
                  <Button onClick={() => setShowApprovalDialog(true)} className="flex-1">
                    <CheckCircle className="mr-2 h-4 w-4" /> Review & Approve
                  </Button>
                </div>
              )}
            </>
          ) : (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-16">
                <Wrench className="h-12 w-12 text-muted-foreground mb-4" />
                <p className="text-muted-foreground">Select a project and describe a task to get started</p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* Task History */}
      {tasks.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Task History</CardTitle>
            <CardDescription>Recent software engineering tasks</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {tasks.map((task) => (
                <div
                  key={task.task_id}
                  className={`flex items-center justify-between p-3 rounded-lg cursor-pointer transition-colors ${
                    selectedTask?.task_id === task.task_id
                      ? "bg-accent/10 border border-accent"
                      : "bg-muted hover:bg-muted/80"
                  }`}
                  onClick={() => setSelectedTask(task)}
                >
                  <div className="flex items-center gap-3">
                    {getStateIcon(task.state)}
                    <div>
                      <p className="font-medium text-sm">{task.task_description}</p>
                      <p className="text-xs text-muted-foreground">
                        {TASK_TYPES.find((t) => t.value === task.task_type)?.label || task.task_type}
                        {" • "}
                        {projects.find((p) => p.id === task.repository_id)?.name || task.repository_id}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge className={STATE_COLORS[task.state]}>{task.state.replace("_", " ")}</Badge>
                    <span className="text-xs text-muted-foreground">
                      {new Date(task.started_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Approval Dialog */}
      <Dialog open={showApprovalDialog} onOpenChange={setShowApprovalDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Review Implementation</DialogTitle>
            <DialogDescription>Review the generated code and approve or reject.</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            {selectedTask?.review_result && (
              <div className="p-4 rounded-lg bg-muted">
                <div className="flex items-center gap-2 mb-2">
                  {selectedTask.review_result.passed ? (
                    <CheckCircle className="h-5 w-5 text-green-500" />
                  ) : (
                    <XCircle className="h-5 w-5 text-red-500" />
                  )}
                  <span className="font-medium">Score: {selectedTask.review_result.score}/100</span>
                </div>
                <p className="text-sm text-muted-foreground">{selectedTask.review_result.summary}</p>
              </div>
            )}
            {selectedTask?.commit_summary && (
              <div className="p-4 rounded-lg bg-muted">
                <h4 className="font-medium mb-2">Commit Message</h4>
                <p className="font-mono text-sm">{selectedTask.commit_summary.message}</p>
              </div>
            )}
          </div>
          <DialogFooter className="flex gap-2">
            <Button variant="outline" onClick={() => rejectTask("Needs changes")}>
              <XCircle className="mr-2 h-4 w-4" /> Reject
            </Button>
            <Button onClick={approveTask}>
              <CheckCircle className="mr-2 h-4 w-4" /> Approve
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
