'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useAgentStore } from '@/stores/agent-store';
import { useProjectStore } from '@/stores/project-store';
import type { AgentType } from '@/types/agents';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Bot,
  CheckCircle,
  XCircle,
  Clock,
  Loader2,
  Code,
  Shield,
  GitBranch,
  ListChecks,
  Search,
  Play,
  Send,
  X,
  ArrowRight,
  Upload,
  GitMerge,
  Sparkles,
  FolderKanban,
} from 'lucide-react';
import { TaskResult } from '@/components/task-result';

const AGENT_INFO: Record<string, { icon: any; color: string; role: string; whatTheyDo: string; placeholder: string; suggestedTasks: string[] }> = {
  reviewer: {
    icon: Shield,
    color: 'text-purple-500',
    role: 'Code Quality Guard',
    whatTheyDo: 'Scans code for bugs, security vulnerabilities, anti-patterns, and style issues.',
    placeholder: 'e.g., Review the authentication module for security issues',
    suggestedTasks: [
      'Scan the codebase for security vulnerabilities',
      'Review code style and anti-patterns',
      'Check for hardcoded secrets or API keys',
      'Analyze error handling patterns',
    ],
  },
  executor: {
    icon: Code,
    color: 'text-blue-500',
    role: 'Builder & Fixer',
    whatTheyDo: 'Writes new code, refactors existing code, fixes bugs, and implements features.',
    placeholder: 'e.g., Add input validation to the user registration endpoint',
    suggestedTasks: [
      'Fix the failing unit tests',
      'Refactor the database query layer',
      'Add TypeScript types to untyped modules',
      'Implement a caching layer for API responses',
    ],
  },
  devops: {
    icon: GitBranch,
    color: 'text-orange-500',
    role: 'Infrastructure Specialist',
    whatTheyDo: 'Analyzes deployment readiness, generates Dockerfiles, CI/CD pipelines, and configs.',
    placeholder: 'e.g., Generate a Docker Compose setup for this project',
    suggestedTasks: [
      'Generate a Dockerfile for this project',
      'Create a GitHub Actions CI/CD pipeline',
      'Analyze deployment readiness',
      'Set up environment configuration',
    ],
  },
  planner: {
    icon: ListChecks,
    color: 'text-green-500',
    role: 'Task Architect',
    whatTheyDo: 'Breaks complex projects into smaller actionable steps with dependencies.',
    placeholder: 'e.g., Create a migration plan from REST to GraphQL',
    suggestedTasks: [
      'Break down the refactoring into phases',
      'Create a dependency map for modules',
      'Plan a database migration strategy',
      'Design the API versioning approach',
    ],
  },
  researcher: {
    icon: Search,
    color: 'text-cyan-500',
    role: 'Knowledge Gatherer',
    whatTheyDo: 'Explores codebases, finds patterns, gathers context for other agents.',
    placeholder: 'e.g., Find all API endpoints and their authentication requirements',
    suggestedTasks: [
      'Map all API endpoints and their auth requirements',
      'Find all database models and relationships',
      'Identify third-party dependencies and versions',
      'Analyze the project architecture patterns',
    ],
  },
};

export default function AgentsPage() {
  const { agents, tasks, metrics, isLoading, fetchAgents, fetchMetrics, fetchTasks, createTask } =
    useAgentStore();
  const { projects } = useProjectStore();
  const [showTasks, setShowTasks] = useState(false);
  const [runDialog, setRunDialog] = useState<string | null>(null);
  const [taskDescription, setTaskDescription] = useState('');
  const [selectedProjectId, setSelectedProjectId] = useState<string>('');
  const [running, setRunning] = useState(false);
  const [runResult, setRunResult] = useState<{ success: boolean; message: string } | null>(null);

  useEffect(() => {
    fetchAgents();
    fetchMetrics();
    fetchTasks();
  }, [fetchAgents, fetchMetrics, fetchTasks]);

  useEffect(() => {
    const hasRunning = tasks.some((t: any) => t.status === 'running' || t.status === 'queued');
    if (!hasRunning) return;
    const interval = setInterval(() => {
      fetchTasks();
      fetchMetrics();
    }, 2000);
    return () => clearInterval(interval);
  }, [tasks, fetchTasks, fetchMetrics]);

  const handleRunAgent = async () => {
    if (!runDialog || !taskDescription.trim()) return;
    setRunning(true);
    setRunResult(null);
    try {
      const project = projects.find(p => p.id === selectedProjectId);
      const contextParts = [taskDescription];
      if (project) {
        contextParts.unshift(`Project: ${project.name}`);
        const langs = project.languages;
        if (Array.isArray(langs) && langs.length) {
          contextParts.push(`Languages: ${langs.map((l: any) => l.name || l).join(', ')}`);
        } else if (typeof langs === 'number') {
          contextParts.push(`${langs} languages detected`);
        }
      }
      await createTask({
        title: `${AGENT_INFO[runDialog]?.role || runDialog} Task`,
        description: contextParts.join('\n'),
        task_description: contextParts.join('\n'),
        agent_type: runDialog as AgentType,
      } as any);
      setRunResult({ success: true, message: 'Task assigned successfully! The agent will process it shortly.' });
      setTaskDescription('');
      fetchTasks();
      fetchMetrics();
    } catch {
      setRunResult({ success: false, message: 'Failed to assign task. Please try again.' });
    } finally {
      setRunning(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'idle': return <Badge variant="secondary">Idle</Badge>;
      case 'running': return <Badge className="bg-blue-500">Running</Badge>;
      case 'error': return <Badge variant="destructive">Error</Badge>;
      default: return <Badge>{status}</Badge>;
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'idle': return <Clock className="h-4 w-4 text-muted-foreground" />;
      case 'running': return <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />;
      case 'error': return <XCircle className="h-4 w-4 text-red-500" />;
      default: return <Bot className="h-4 w-4" />;
    }
  };

  const selectedAgent = runDialog ? AGENT_INFO[runDialog] : null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">AI Agents</h1>
        <p className="text-muted-foreground">
          Your team of specialized AI workers — give them tasks and they'll work for you
        </p>
      </div>

      {/* How It Works */}
      <Card className="border-accent/30 bg-accent/5">
        <CardContent className="pt-6">
          <h3 className="font-semibold text-sm mb-3 flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-accent" /> How It Works
          </h3>
          <div className="flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
            <div className="flex items-center gap-2">
              <div className="flex h-7 w-7 items-center justify-center rounded-full bg-accent/20 text-accent text-xs font-bold">1</div>
              <Upload className="h-4 w-4" />
              <span>Import a Repository</span>
            </div>
            <ArrowRight className="h-4 w-4 text-text-muted hidden sm:block" />
            <div className="flex items-center gap-2">
              <div className="flex h-7 w-7 items-center justify-center rounded-full bg-accent/20 text-accent text-xs font-bold">2</div>
              <GitMerge className="h-4 w-4" />
              <span>Workflow Auto-Created</span>
            </div>
            <ArrowRight className="h-4 w-4 text-text-muted hidden sm:block" />
            <div className="flex items-center gap-2">
              <div className="flex h-7 w-7 items-center justify-center rounded-full bg-accent/20 text-accent text-xs font-bold">3</div>
              <Play className="h-4 w-4" />
              <span>Run an Agent on It</span>
            </div>
          </div>
          <div className="flex gap-2 mt-3">
            <Link href="/repositories">
              <Button variant="outline" size="sm"><Upload className="h-4 w-4 mr-1" /> Import Repo</Button>
            </Link>
            <Link href="/workflows">
              <Button variant="outline" size="sm"><GitMerge className="h-4 w-4 mr-1" /> View Workflows</Button>
            </Link>
            {projects.length > 0 && (
              <Link href={`/projects/${projects[0].id}`}>
                <Button variant="outline" size="sm"><FolderKanban className="h-4 w-4 mr-1" /> Latest Project</Button>
              </Link>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Metrics */}
      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <Card key={i}><CardHeader className="pb-2"><Skeleton className="h-4 w-24" /></CardHeader><CardContent><Skeleton className="h-8 w-16" /></CardContent></Card>
          ))}
        </div>
      ) : metrics ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card><CardContent className="pt-6"><div className="flex items-center space-x-3"><Bot className="h-8 w-8 text-blue-500" /><div><p className="text-2xl font-bold">{metrics.total_agents}</p><p className="text-xs text-text-muted">Total Agents</p></div></div></CardContent></Card>
          <Card><CardContent className="pt-6"><div className="flex items-center space-x-3"><Clock className="h-8 w-8 text-green-500" /><div><p className="text-2xl font-bold">{metrics.idle_agents}</p><p className="text-xs text-text-muted">Idle</p></div></div></CardContent></Card>
          <Card><CardContent className="pt-6"><div className="flex items-center space-x-3"><Loader2 className="h-8 w-8 text-blue-500" /><div><p className="text-2xl font-bold">{metrics.running_tasks}</p><p className="text-xs text-text-muted">Running Tasks</p></div></div></CardContent></Card>
          <Card><CardContent className="pt-6"><div className="flex items-center space-x-3"><CheckCircle className="h-8 w-8 text-green-500" /><div><p className="text-2xl font-bold">{metrics.completed_tasks}</p><p className="text-xs text-text-muted">Completed</p></div></div></CardContent></Card>
        </div>
      ) : null}

      {/* Agent Cards */}
      <Card>
        <CardHeader><CardTitle>Your AI Team</CardTitle></CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-4">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="flex items-center space-x-4">
                  <Skeleton className="h-10 w-10 rounded-full" />
                  <div className="space-y-2"><Skeleton className="h-4 w-32" /><Skeleton className="h-3 w-48" /></div>
                </div>
              ))}
            </div>
          ) : agents.length > 0 ? (
            <div className="space-y-4">
              {agents.map((agent) => {
                const info = AGENT_INFO[agent.agent_type] || { icon: Bot, color: 'text-text-muted', role: agent.agent_type, whatTheyDo: agent.description, placeholder: 'Describe the task...', suggestedTasks: [] };
                const Icon = info.icon;
                return (
                  <div key={agent.id} className="p-5 border rounded-lg hover:border-text-muted transition-colors">
                    <div className="flex items-start justify-between">
                      <div className="flex items-start space-x-4">
                        <div className="p-2.5 bg-muted rounded-lg">
                          <Icon className={`h-5 w-5 ${info.color}`} />
                        </div>
                        <div className="space-y-1">
                          <div className="flex items-center space-x-2">
                            <p className="font-semibold text-lg">{agent.name}</p>
                            <Badge variant="outline" className="text-xs">{agent.agent_type}</Badge>
                          </div>
                          <p className="text-sm text-accent font-medium">{info.role}</p>
                          <p className="text-sm text-muted-foreground max-w-xl">{info.whatTheyDo}</p>
                          <div className="flex flex-wrap gap-1.5 mt-2">
                            {(agent.capabilities || []).map((cap: string) => (
                              <Badge key={cap} variant="secondary" className="text-xs">{cap.replace(/_/g, ' ')}</Badge>
                            ))}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center space-x-3">
                        {getStatusBadge(agent.status)}
                        <Button
                          size="sm"
                          onClick={() => {
                            setRunDialog(agent.agent_type);
                            setRunResult(null);
                            setTaskDescription(info.suggestedTasks[0] || '');
                            if (projects.length > 0 && !selectedProjectId) {
                              setSelectedProjectId(projects[0].id);
                            }
                          }}
                        >
                          <Play className="h-4 w-4 mr-1" /> Run
                        </Button>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <p className="text-muted-foreground text-center py-8">No agents available</p>
          )}
        </CardContent>
      </Card>

      {/* Run Agent Dialog */}
      {runDialog && selectedAgent && (
        <Card className="border-accent">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="flex items-center space-x-2">
              <Send className="h-5 w-5" />
              <span>Assign Task to {agents.find(a => a.agent_type === runDialog)?.name || runDialog}</span>
            </CardTitle>
            <Button variant="ghost" size="icon" onClick={() => { setRunDialog(null); setRunResult(null); }}>
              <X className="h-4 w-4" />
            </Button>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-muted-foreground">{selectedAgent.whatTheyDo}</p>

            {/* Project selector */}
            {projects.length > 0 && (
              <div>
                <label className="text-sm font-medium mb-1 block">Target Project (optional)</label>
                <select
                  className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-text focus:border-accent focus:outline-none"
                  value={selectedProjectId}
                  onChange={(e) => setSelectedProjectId(e.target.value)}
                >
                  <option value="">No specific project</option>
                  {projects.map(p => (
                    <option key={p.id} value={p.id}>{p.name}</option>
                  ))}
                </select>
              </div>
            )}

            {/* Task description */}
            <div>
              <label className="text-sm font-medium mb-1 block">What should this agent do?</label>
              <textarea
                className="w-full min-h-[100px] rounded-md border border-border bg-surface px-3 py-2 text-sm text-text placeholder:text-text-muted focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
                placeholder={selectedAgent.placeholder}
                value={taskDescription}
                onChange={(e) => setTaskDescription(e.target.value)}
              />
            </div>

            {/* Suggested tasks */}
            {selectedAgent.suggestedTasks.length > 0 && (
              <div>
                <p className="text-xs text-text-muted mb-2">Quick suggestions:</p>
                <div className="flex flex-wrap gap-1.5">
                  {selectedAgent.suggestedTasks.map((st, i) => (
                    <Button key={i} variant="outline" size="sm" className="text-xs h-7" onClick={() => setTaskDescription(st)}>
                      {st}
                    </Button>
                  ))}
                </div>
              </div>
            )}

            {runResult && (
              <div className={`p-3 rounded-md text-sm ${runResult.success ? 'bg-green-500/10 text-green-500 border border-green-500/20' : 'bg-red-500/10 text-red-500 border border-red-500/20'}`}>
                {runResult.message}
              </div>
            )}

            <div className="flex justify-end space-x-2">
              <Button variant="outline" onClick={() => { setRunDialog(null); setRunResult(null); }}>Cancel</Button>
              <Button onClick={handleRunAgent} isLoading={running} disabled={!taskDescription.trim()}>
                <Send className="h-4 w-4 mr-1" /> Assign Task
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Recent Tasks */}
      {tasks.length > 0 && (
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Recent Tasks</CardTitle>
            <Button variant="ghost" size="sm" onClick={() => setShowTasks(!showTasks)}>
              {showTasks ? 'Hide' : `Show (${tasks.length})`}
            </Button>
          </CardHeader>
          {showTasks && (
            <CardContent>
              <div className="space-y-3">
                {tasks.slice(0, 10).map((task) => {
                  const t = task as any;
                  return (
                  <div key={t.id} className="border rounded-lg overflow-hidden">
                    <div className="flex items-center justify-between p-3">
                      <div className="flex items-center space-x-3">
                        {getStatusIcon(t.status)}
                        <div>
                          <p className="text-sm font-medium">{t.agent_type}</p>
                          <p className="text-xs text-muted-foreground">{t.description}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {t.duration && <span className="text-xs text-muted-foreground">{t.duration}s</span>}
                        {getStatusBadge(t.status)}
                      </div>
                    </div>
                    {t.result && (
                      <TaskResult content={t.result} status={t.status} />
                    )}
                  </div>
                  );
                })}
              </div>
            </CardContent>
          )}
        </Card>
      )}
    </div>
  );
}
