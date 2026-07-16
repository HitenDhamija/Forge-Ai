'use client';

import { useEffect, useState, useRef, useCallback, useMemo, Suspense } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { useWorkflowStore } from '@/stores/workflow-store';
import { useProjectStore } from '@/stores/project-store';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Skeleton } from '@/components/ui/skeleton';
import { PageHeader } from '@/components/layouts/page-header';
import { TaskResult } from '@/components/task-result';
import {
  CheckCircle2,
  XCircle,
  Clock,
  Loader2,
  Pause,
  Play,
  X,
  Plus,
  Trash2,
  ChevronRight,
  Zap,
  FileText,
  Trash,
  Search,
  GitBranch,
  Shield,
  TestTube,
  BarChart3,
  Settings,
  Package,
  Bug,
  Rocket,
  RotateCcw,
  Sparkles,
  FolderKanban,
} from 'lucide-react';

const STEP_ICONS = [Search, GitBranch, Shield, TestTube, BarChart3, Settings, Package, Bug, Rocket, Sparkles];

export default function WorkflowsPage() {
  return (
    <Suspense fallback={<div className="p-6 text-text-muted">Loading workflows...</div>}>
      <WorkflowsPageContent />
    </Suspense>
  );
}

function WorkflowsPageContent() {
  const searchParams = useSearchParams();
  const projectIdFromUrl = searchParams.get('project_id');

  const {
    workflows,
    isLoading,
    fetchWorkflows,
    createWorkflow,
    approveWorkflow,
    startWorkflow,
    pauseWorkflow,
    resumeWorkflow,
    cancelWorkflow,
    deleteWorkflow,
  } = useWorkflowStore();

  const { selectedProject, projects, selectProject } = useProjectStore();

  // Auto-select project from URL param
  useEffect(() => {
    if (projectIdFromUrl) {
      const project = projects.find((p) => p.id === projectIdFromUrl);
      if (project && (!selectedProject || selectedProject.id !== projectIdFromUrl)) {
        selectProject(project);
      }
    }
  }, [projectIdFromUrl, projects, selectedProject, selectProject]);

  const activeProjectId = projectIdFromUrl || selectedProject?.id || null;

  const [showCreate, setShowCreate] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [taskInputs, setTaskInputs] = useState([{ title: '', description: '' }]);
  const [creating, setCreating] = useState(false);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const hasRunning = workflows.some((w) => w.status === 'running');

  const uniqueWorkflows = useMemo(() => {
    const seen = new Set<string>();
    return workflows.filter((w) => {
      if (seen.has(w.id)) return false;
      seen.add(w.id);
      return true;
    });
  }, [workflows]);

  const startPolling = useCallback(() => {
    if (pollingRef.current) return;
    pollingRef.current = setInterval(() => {
      fetchWorkflows(activeProjectId ? { project_id: activeProjectId } : undefined);
    }, 2000);
  }, [fetchWorkflows, activeProjectId]);

  const stopPolling = useCallback(() => {
    if (pollingRef.current) { clearInterval(pollingRef.current); pollingRef.current = null; }
  }, []);

  useEffect(() => {
    fetchWorkflows(activeProjectId ? { project_id: activeProjectId } : undefined);
  }, [fetchWorkflows, activeProjectId]);
  useEffect(() => {
    if (hasRunning) startPolling(); else stopPolling();
    return stopPolling;
  }, [hasRunning, startPolling, stopPolling]);

  const addTaskInput = () => setTaskInputs([...taskInputs, { title: '', description: '' }]);
  const removeTaskInput = (i: number) => setTaskInputs(taskInputs.filter((_, idx) => idx !== i));
  const updateTaskInput = (i: number, field: 'title' | 'description', val: string) => {
    const u = [...taskInputs]; u[i][field] = val; setTaskInputs(u);
  };

  const handleCreate = async () => {
    if (!newTitle.trim()) return;
    setCreating(true);
    try {
      await createWorkflow({
        title: newTitle,
        description: newDesc,
        tasks: taskInputs.filter(t => t.title.trim()),
        project_id: activeProjectId || undefined,
      });
      setNewTitle(''); setNewDesc(''); setTaskInputs([{ title: '', description: '' }]); setShowCreate(false);
    } catch {} finally { setCreating(false); }
  };

  const getTaskProgress = (wf: any) => {
    const tasks = wf.tasks || [];
    if (tasks.length === 0) return { completed: 0, total: 0, percent: 0, failed: 0 };
    const completed = tasks.filter((t: any) => t.status === 'completed').length;
    const failed = tasks.filter((t: any) => t.status === 'failed').length;
    return { completed, total: tasks.length, percent: Math.round(((completed + failed) / tasks.length) * 100), failed };
  };

  const getStepConfig = (status: string) => {
    switch (status) {
      case 'completed': return { ring: 'border-success bg-success/15 shadow-lg shadow-success/20', icon: 'text-success', line: 'bg-success', glow: 'shadow-success/30' };
      case 'failed': return { ring: 'border-danger bg-danger/15 shadow-lg shadow-danger/20', icon: 'text-danger', line: 'bg-danger', glow: 'shadow-danger/30' };
      case 'running': return { ring: 'border-blue-400 bg-blue-500/15 shadow-lg shadow-blue-500/30 animate-pulse', icon: 'text-blue-400', line: 'bg-gradient-to-b from-blue-500 to-border', glow: 'shadow-blue-500/30' };
      default: return { ring: 'border-border bg-surface hover:border-text-muted hover:bg-surface-hover', icon: 'text-text-muted', line: 'bg-border', glow: '' };
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed': return <Badge className="bg-success text-white border-0">Completed</Badge>;
      case 'failed': return <Badge className="bg-danger text-white border-0">Failed</Badge>;
      case 'running': return <Badge className="bg-blue-500 text-white border-0 animate-pulse">Running</Badge>;
      case 'paused': return <Badge className="bg-warning text-black border-0">Paused</Badge>;
      case 'ready': return <Badge className="bg-purple-500 text-white border-0">Ready</Badge>;
      case 'cancelled': return <Badge variant="secondary">Cancelled</Badge>;
      default: return <Badge variant="outline">Draft</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Workflows"
        description="Create, approve, and run automated pipelines"
        actions={
          <Button onClick={() => setShowCreate(!showCreate)}>
            <Plus className="mr-2 h-4 w-4" /> New Pipeline
          </Button>
        }
      />

      {showCreate && (
        <Card className="border-accent/30">
          <CardContent className="pt-6 space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <Input label="Pipeline Name" placeholder="e.g., Code Quality Pipeline" value={newTitle} onChange={e => setNewTitle(e.target.value)} />
              <Input label="Description" placeholder="What does this pipeline do?" value={newDesc} onChange={e => setNewDesc(e.target.value)} />
            </div>
            <div>
              <p className="text-sm font-medium mb-3 text-text-secondary">Pipeline Steps</p>
              {taskInputs.map((task, i) => (
                <div key={i} className="flex items-center gap-3 mb-3">
                  <span className="flex items-center justify-center w-8 h-8 rounded-full bg-accent/20 text-accent text-sm font-bold shrink-0">
                    {i + 1}
                  </span>
                  <Input placeholder={`Step ${i + 1} title`} value={task.title} onChange={e => updateTaskInput(i, 'title', e.target.value)} className="flex-1" />
                  <Input placeholder="Description" value={task.description} onChange={e => updateTaskInput(i, 'description', e.target.value)} className="flex-1" />
                  {taskInputs.length > 1 && (
                    <Button variant="ghost" size="icon" onClick={() => removeTaskInput(i)}>
                      <Trash2 className="h-4 w-4 text-danger" />
                    </Button>
                  )}
                </div>
              ))}
              <Button variant="outline" size="sm" onClick={addTaskInput} className="mt-2">
                <Plus className="mr-1 h-3 w-3" /> Add Step
              </Button>
            </div>
            <div className="flex justify-end space-x-2 pt-2">
              <Button variant="outline" onClick={() => setShowCreate(false)}>Cancel</Button>
              <Button onClick={handleCreate} isLoading={creating}>Create Pipeline</Button>
            </div>
          </CardContent>
        </Card>
      )}

      {isLoading && workflows.length === 0 ? (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <Card key={i}><CardContent className="pt-6"><Skeleton className="h-8 w-48 mb-4" /><Skeleton className="h-4 w-full mb-2" /><Skeleton className="h-4 w-3/4" /></CardContent></Card>
          ))}
        </div>
      ) : workflows.length === 0 ? (
        <Card>
          <CardContent className="pt-6">
            <div className="text-center py-12">
              <FileText className="h-12 w-12 mx-auto text-text-muted mb-4" />
              <p className="text-lg font-medium mb-1">No workflows yet</p>
              <p className="text-sm text-text-muted mb-4">Import a repository to auto-create a pipeline.</p>
              <Button onClick={() => setShowCreate(true)}><Plus className="mr-2 h-4 w-4" /> Create Pipeline</Button>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-6">
          {uniqueWorkflows.map((wf) => {
            const isRunning = wf.status === 'running';
            const progress = getTaskProgress(wf);
            const tasks = wf.tasks || [];

            return (
              <Card key={wf.id} className={`overflow-hidden transition-all duration-300 ${isRunning ? 'ring-2 ring-blue-500/40 shadow-lg shadow-blue-500/10' : 'hover:shadow-lg hover:shadow-black/20'}`}>

                {/* ── Pipeline Header ── */}
                <div className={`relative p-6 ${
                  wf.status === 'completed' ? 'bg-gradient-to-r from-success/10 via-success/5 to-transparent' :
                  wf.status === 'failed' ? 'bg-gradient-to-r from-danger/10 via-danger/5 to-transparent' :
                  wf.status === 'running' ? 'bg-gradient-to-r from-blue-500/10 via-blue-500/5 to-transparent' :
                  wf.status === 'ready' ? 'bg-gradient-to-r from-purple-500/10 via-purple-500/5 to-transparent' :
                  'bg-gradient-to-r from-surface to-transparent'
                }`}>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      {/* Status icon */}
                      <div className={`relative p-3 rounded-2xl ${
                        wf.status === 'completed' ? 'bg-success/20' :
                        wf.status === 'failed' ? 'bg-danger/20' :
                        wf.status === 'running' ? 'bg-blue-500/20' :
                        wf.status === 'ready' ? 'bg-purple-500/20' :
                        'bg-surface-hover'
                      }`}>
                        {wf.status === 'running' ? (
                          <Loader2 className="h-7 w-7 text-blue-400 animate-spin" />
                        ) : wf.status === 'completed' ? (
                          <CheckCircle2 className="h-7 w-7 text-success" />
                        ) : wf.status === 'failed' ? (
                          <XCircle className="h-7 w-7 text-danger" />
                        ) : wf.status === 'ready' ? (
                          <Zap className="h-7 w-7 text-purple-400" />
                        ) : (
                          <Clock className="h-7 w-7 text-text-muted" />
                        )}
                        {isRunning && (
                          <span className="absolute -top-1 -right-1 h-3 w-3 rounded-full bg-blue-500 animate-ping" />
                        )}
                      </div>
                      <div>
                        <div className="flex items-center gap-3">
                          <h3 className="text-xl font-bold">{wf.title}</h3>
                          {getStatusBadge(wf.status)}
                          <Badge variant="outline" className="text-xs">{tasks.length} steps</Badge>
                        </div>
                        {wf.project_id && (
                          <Link href={`/projects/${wf.project_id}`} className="inline-flex items-center gap-1 text-xs text-accent hover:text-accent-hover mt-0.5">
                            <FolderKanban className="h-3 w-3" />
                            View Project
                          </Link>
                        )}
                        {wf.description && <p className="text-sm text-text-muted mt-0.5">{wf.description}</p>}
                        <p className="text-xs text-text-muted mt-1">
                          Created {new Date(wf.created_at).toLocaleDateString()} at {new Date(wf.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center space-x-2">
                      {wf.status === 'draft' && (
                        <Button onClick={() => approveWorkflow(wf.id)}>
                          <CheckCircle2 className="mr-1.5 h-4 w-4" /> Approve
                        </Button>
                      )}
                      {wf.status === 'ready' && (
                        <Button onClick={() => startWorkflow(wf.id)} className="bg-success hover:bg-success/90">
                          <Play className="mr-1.5 h-4 w-4" /> Run Pipeline
                        </Button>
                      )}
                      {isRunning && (
                        <>
                          <Button variant="outline" onClick={() => pauseWorkflow(wf.id)}><Pause className="mr-1.5 h-4 w-4" /> Pause</Button>
                          <Button variant="outline" onClick={() => cancelWorkflow(wf.id)} className="text-danger hover:text-danger"><X className="mr-1.5 h-4 w-4" /> Cancel</Button>
                        </>
                      )}
                      {wf.status === 'paused' && (
                        <Button onClick={() => resumeWorkflow(wf.id)}><RotateCcw className="mr-1.5 h-4 w-4" /> Resume</Button>
                      )}
                      <Link href={`/workflows/${wf.id}`}>
                        <Button variant="ghost" size="sm">Details <ChevronRight className="ml-1 h-4 w-4" /></Button>
                      </Link>
                      {wf.status !== 'running' && (
                        <Button variant="ghost" size="icon" onClick={() => { if (confirm(`Delete "${wf.title}"?`)) deleteWorkflow(wf.id); }}>
                          <Trash className="h-4 w-4 text-danger" />
                        </Button>
                      )}
                    </div>
                  </div>
                </div>

                {/* ── Progress Bar ── */}
                {(wf.status === 'running' || wf.status === 'completed' || wf.status === 'failed') && (
                  <div className="px-6 py-3 bg-surface/50 border-t border-border">
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-xs font-medium text-text-muted">
                        {progress.completed}/{progress.total} steps completed
                        {progress.failed > 0 && <span className="text-danger ml-2">{progress.failed} failed</span>}
                      </span>
                      <span className="text-xs font-bold text-text-muted">{progress.percent}%</span>
                    </div>
                    <div className="h-2.5 w-full rounded-full bg-surface overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all duration-700 ease-out ${
                          wf.status === 'failed' ? 'bg-gradient-to-r from-danger/80 to-danger' :
                          wf.status === 'completed' ? 'bg-gradient-to-r from-success/80 to-success' :
                          'bg-gradient-to-r from-blue-400 to-blue-500'
                        }`}
                        style={{ width: `${progress.percent}%` }}
                      />
                    </div>
                  </div>
                )}

                {/* ── Visual Stepper ── */}
                {tasks.length > 0 && (
                  <div className="p-6">
                    <div className="space-y-0">
                      {tasks.map((task: any, i: number) => {
                        const isLast = i === tasks.length - 1;
                        const sc = getStepConfig(task.status);
                        const StepIcon = STEP_ICONS[i % STEP_ICONS.length];

                        return (
                          <div key={task.id || i} className="flex group/step">
                            {/* ── Stepper Column ── */}
                            <div className="flex flex-col items-center mr-5">
                              {/* Circle */}
                              <div className={`relative flex items-center justify-center w-12 h-12 rounded-2xl border-2 shrink-0 z-10 transition-all duration-300 ${sc.ring}`}>
                                {task.status === 'completed' && <CheckCircle2 className="h-5 w-5 text-success" />}
                                {task.status === 'failed' && <XCircle className="h-5 w-5 text-danger" />}
                                {task.status === 'running' && <Loader2 className="h-5 w-5 text-blue-400 animate-spin" />}
                                {task.status === 'pending' && (
                                  <StepIcon className="h-5 w-5 text-text-muted group-hover/step:text-accent transition-colors" />
                                )}
                                {/* Step number badge */}
                                <span className={`absolute -top-2 -left-2 w-5 h-5 rounded-full text-[10px] font-bold flex items-center justify-center ${
                                  task.status === 'completed' ? 'bg-success text-white' :
                                  task.status === 'failed' ? 'bg-danger text-white' :
                                  task.status === 'running' ? 'bg-blue-500 text-white' :
                                  'bg-surface-hover text-text-muted border border-border'
                                }`}>
                                  {i + 1}
                                </span>
                              </div>
                              {/* Connecting Line */}
                              {!isLast && (
                                <div className={`w-0.5 flex-1 min-h-[2.5rem] transition-all duration-500 ${sc.line}`} />
                              )}
                            </div>

                            {/* ── Step Content ── */}
                            <div className={`flex-1 ${isLast ? '' : 'pb-5'}`}>
                              <div className={`rounded-xl border p-4 transition-all duration-300 ${
                                task.status === 'running' ? 'border-blue-500/40 bg-blue-500/5 shadow-md shadow-blue-500/10' :
                                task.status === 'completed' ? 'border-success/30 bg-success/5' :
                                task.status === 'failed' ? 'border-danger/30 bg-danger/5' :
                                'border-border bg-surface/50 hover:bg-surface-hover/50 hover:border-text-muted/30'
                              }`}>
                                <div className="flex items-center justify-between">
                                  <div className="flex-1">
                                    <p className={`text-sm font-semibold ${
                                      task.status === 'completed' ? 'text-success' :
                                      task.status === 'failed' ? 'text-danger' :
                                      task.status === 'running' ? 'text-blue-400' :
                                      'text-text'
                                    }`}>
                                      {task.title}
                                    </p>
                                    {task.description && (
                                      <p className="text-xs text-text-muted mt-0.5">{task.description}</p>
                                    )}
                                  </div>
                                  <div className="flex items-center gap-2 ml-4">
                                    {task.duration != null && (
                                      <span className="text-xs font-mono text-text-muted">{task.duration}s</span>
                                    )}
                                    <Badge variant={
                                      task.status === 'completed' ? 'success' :
                                      task.status === 'failed' ? 'destructive' :
                                      task.status === 'running' ? 'default' :
                                      'outline'
                                    } className="text-xs capitalize">
                                      {task.status === 'running' && <Loader2 className="mr-1 h-3 w-3 animate-spin" />}
                                      {task.status || 'pending'}
                                    </Badge>
                                  </div>
                                </div>

                                {task.result && (
                                  <TaskResult content={task.result} status={task.status} />
                                )}
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
