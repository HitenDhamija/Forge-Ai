'use client';

import { useEffect, useState, useRef, useCallback } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { useWorkflowStore } from '@/stores/workflow-store';
import { workflowService } from '@/services/workflow.service';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { TaskResult } from '@/components/task-result';
import { Skeleton } from '@/components/ui/skeleton';
import {
  ArrowLeft,
  CheckCircle2,
  XCircle,
  Clock,
  Loader2,
  Pause,
  Play,
  RotateCcw,
  Zap,
  Timer,
  Search,
  GitBranch,
  Shield,
  TestTube,
  BarChart3,
  Settings,
  Package,
  Bug,
  Rocket,
  Sparkles,
  CheckCircle,
  MessageSquare,
  Download,
  AlertTriangle,
  AlertCircle,
  Info,
  Lightbulb,
  Send,
} from 'lucide-react';

const STEP_ICONS = [Search, GitBranch, Shield, TestTube, BarChart3, Settings, Package, Bug, Rocket, Sparkles];

const BACKEND = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api/v1';

export default function WorkflowDetailPage() {
  const params = useParams();
  const workflowId = params.id as string;
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const [localWf, setLocalWf] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState<any>(null);
  const [aiQuery, setAiQuery] = useState('');
  const [aiResponse, setAiResponse] = useState('');
  const [aiLoading, setAiLoading] = useState(false);
  const [expandedTasks, setExpandedTasks] = useState<Set<number>>(new Set());

  const { approveWorkflow, startWorkflow, pauseWorkflow, resumeWorkflow, cancelWorkflow } = useWorkflowStore();

  const loadWorkflow = useCallback(async () => {
    if (!workflowId) return;
    try {
      const data = await workflowService.getWorkflow(workflowId);
      setLocalWf(data);
      if (data?.summary) setSummary(data.summary);
    } catch {
      setLocalWf(null);
    } finally {
      setLoading(false);
    }
  }, [workflowId]);

  useEffect(() => { loadWorkflow(); }, [loadWorkflow]);

  const isRunning = localWf?.status === 'running';
  const isPaused = localWf?.status === 'paused';

  useEffect(() => {
    if (isRunning) {
      pollingRef.current = setInterval(loadWorkflow, 1500);
    }
    return () => { if (pollingRef.current) { clearInterval(pollingRef.current); pollingRef.current = null; } };
  }, [isRunning, loadWorkflow]);

  const toggleTask = (idx: number) => {
    setExpandedTasks(prev => {
      const next = new Set(prev);
      if (next.has(idx)) next.delete(idx);
      else next.add(idx);
      return next;
    });
  };

  const handleAskAI = async (query: string) => {
    setAiLoading(true);
    setAiResponse('');
    try {
      const r = await fetch(`${BACKEND}/workflows/${workflowId}/ask-ai`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query }),
      });
      const data = await r.json();
      setAiResponse(data?.data?.response || 'No response');
    } catch (e) {
      setAiResponse('Error connecting to AI service.');
    } finally {
      setAiLoading(false);
    }
  };

  const handleExport = () => {
    window.open(`${BACKEND}/workflows/${workflowId}/export`, '_blank');
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-6 w-48" />
        <Skeleton className="h-32 w-full rounded-xl" />
        <div className="grid grid-cols-4 gap-4">{[1,2,3,4].map(i => <Skeleton key={i} className="h-20" />)}</div>
        <Skeleton className="h-96 w-full rounded-xl" />
      </div>
    );
  }

  if (!localWf) {
    return (
      <div className="text-center py-20">
        <p className="text-text-muted text-lg">Workflow not found.</p>
        <Link href="/workflows"><Button variant="ghost" className="mt-4"><ArrowLeft className="mr-2 h-4 w-4" /> Back</Button></Link>
      </div>
    );
  }

  const tasks = localWf.tasks || [];
  const completedCount = tasks.filter((t: any) => t.status === 'completed').length;
  const failedCount = tasks.filter((t: any) => t.status === 'failed').length;
  const runningCount = tasks.filter((t: any) => t.status === 'running').length;
  const totalDuration = tasks.reduce((sum: number, t: any) => sum + (t.duration || 0), 0);

  const getStepConfig = (status: string) => {
    switch (status) {
      case 'completed': return { ring: 'border-success bg-success/15 shadow-lg shadow-success/20', icon: 'text-success', line: 'bg-success' };
      case 'failed': return { ring: 'border-danger bg-danger/15 shadow-lg shadow-danger/20', icon: 'text-danger', line: 'bg-danger' };
      case 'running': return { ring: 'border-blue-400 bg-blue-500/15 shadow-lg shadow-blue-500/30 animate-pulse', icon: 'text-blue-400', line: 'bg-gradient-to-b from-blue-500 to-border' };
      default: return { ring: 'border-border bg-surface', icon: 'text-text-muted', line: 'bg-border' };
    }
  };

  const getSeverityIcon = (msg: string) => {
    if (msg.includes('ERROR') || msg.includes('CRITICAL') || msg.includes('SECURITY')) return <AlertCircle className="h-4 w-4 text-danger shrink-0 mt-0.5" />;
    if (msg.includes('WARN')) return <AlertTriangle className="h-4 w-4 text-yellow-400 shrink-0 mt-0.5" />;
    return <Info className="h-4 w-4 text-blue-400 shrink-0 mt-0.5" />;
  };

  return (
    <div className="space-y-6">
      <Link href="/workflows" className="inline-flex items-center text-sm text-text-muted hover:text-text transition-colors">
        <ArrowLeft className="mr-1 h-4 w-4" /> Back to Workflows
      </Link>

      {/* ── Header ── */}
      <div className={`relative rounded-2xl border p-6 overflow-hidden ${
        localWf.status === 'completed' ? 'border-success/30 bg-gradient-to-r from-success/10 via-success/5 to-transparent' :
        localWf.status === 'failed' ? 'border-danger/30 bg-gradient-to-r from-danger/10 via-danger/5 to-transparent' :
        localWf.status === 'running' ? 'border-blue-500/30 bg-gradient-to-r from-blue-500/10 via-blue-500/5 to-transparent shadow-lg shadow-blue-500/10' :
        localWf.status === 'ready' ? 'border-purple-500/30 bg-gradient-to-r from-purple-500/10 via-purple-500/5 to-transparent' :
        'border-border bg-gradient-to-r from-surface to-transparent'
      }`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-5">
            <div className={`relative p-3.5 rounded-2xl ${
              localWf.status === 'completed' ? 'bg-success/20' :
              localWf.status === 'failed' ? 'bg-danger/20' :
              localWf.status === 'running' ? 'bg-blue-500/20' :
              localWf.status === 'ready' ? 'bg-purple-500/20' :
              'bg-surface-hover'
            }`}>
              {localWf.status === 'running' ? <Loader2 className="h-8 w-8 text-blue-400 animate-spin" /> :
               localWf.status === 'completed' ? <CheckCircle2 className="h-8 w-8 text-success" /> :
               localWf.status === 'failed' ? <XCircle className="h-8 w-8 text-danger" /> :
               localWf.status === 'ready' ? <Zap className="h-8 w-8 text-purple-400" /> :
               <Clock className="h-8 w-8 text-text-muted" />}
              {isRunning && <span className="absolute -top-1 -right-1 h-3 w-3 rounded-full bg-blue-500 animate-ping" />}
            </div>
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-2xl font-bold">{localWf.title}</h1>
                <Badge variant={localWf.status === 'completed' ? 'success' : localWf.status === 'failed' ? 'destructive' : 'secondary'}>
                  {localWf.status}
                </Badge>
                <Badge variant="outline">{tasks.length} steps</Badge>
              </div>
              {localWf.description && <p className="text-sm text-text-muted mt-1">{localWf.description}</p>}
              <div className="flex items-center gap-4 mt-2 text-xs text-text-muted">
                <span>Created {new Date(localWf.created_at).toLocaleString()}</span>
                {totalDuration > 0 && <span className="flex items-center gap-1"><Timer className="h-3 w-3" />{totalDuration.toFixed(1)}s total</span>}
              </div>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            {localWf.status === 'completed' && (
              <>
                <Button variant="outline" onClick={handleExport}>
                  <Download className="mr-2 h-4 w-4" /> Export Report
                </Button>
                <Button onClick={() => handleAskAI('Summarize my workflow results and tell me what to fix first')}>
                  <MessageSquare className="mr-2 h-4 w-4" /> Ask AI
                </Button>
              </>
            )}
            {localWf.status === 'draft' && (
              <Button onClick={() => { approveWorkflow(workflowId); setTimeout(loadWorkflow, 500); }}>
                <CheckCircle2 className="mr-2 h-4 w-4" /> Approve
              </Button>
            )}
            {localWf.status === 'ready' && (
              <Button onClick={() => { startWorkflow(workflowId); setTimeout(loadWorkflow, 500); }} className="bg-success hover:bg-success/90">
                <Play className="mr-2 h-4 w-4" /> Run Pipeline
              </Button>
            )}
            {isRunning && (
              <>
                <Button variant="outline" onClick={() => { pauseWorkflow(workflowId); setTimeout(loadWorkflow, 500); }}><Pause className="mr-2 h-4 w-4" /> Pause</Button>
                <Button variant="outline" onClick={() => { cancelWorkflow(workflowId); setTimeout(loadWorkflow, 500); }} className="text-danger hover:text-danger"><XCircle className="mr-2 h-4 w-4" /> Cancel</Button>
              </>
            )}
            {isPaused && (
              <Button onClick={() => { resumeWorkflow(workflowId); setTimeout(loadWorkflow, 500); }}><RotateCcw className="mr-2 h-4 w-4" /> Resume</Button>
            )}
          </div>
        </div>
      </div>

      {/* ── Stats ── */}
      <div className="grid gap-4 grid-cols-4">
        {[
          { icon: CheckCircle2, label: 'Completed', value: completedCount, color: 'text-success' },
          { icon: XCircle, label: 'Failed', value: failedCount, color: 'text-danger' },
          { icon: Loader2, label: 'Running', value: runningCount, color: 'text-blue-400' },
          { icon: Timer, label: 'Total Time', value: totalDuration > 0 ? `${totalDuration.toFixed(1)}s` : '—', color: 'text-text-muted' },
        ].map((stat) => (
          <Card key={stat.label}>
            <CardContent className="pt-4 pb-4">
              <div className="flex items-center space-x-3">
                <stat.icon className={`h-5 w-5 ${stat.color} ${stat.label === 'Running' && runningCount > 0 ? 'animate-spin' : ''}`} />
                <div>
                  <p className="text-2xl font-bold">{stat.value}</p>
                  <p className="text-xs text-text-muted">{stat.label}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* ── Progress Bar ── */}
      {(localWf.status === 'running' || localWf.status === 'completed' || localWf.status === 'failed') && (
        <Card>
          <CardContent className="pt-4 pb-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-text-muted">Pipeline Progress</span>
              <span className="text-sm font-bold">{completedCount + failedCount}/{tasks.length} ({Math.round(((completedCount + failedCount) / tasks.length) * 100)}%)</span>
            </div>
            <div className="h-3 w-full rounded-full bg-surface overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-700 ease-out ${
                  localWf.status === 'failed' ? 'bg-gradient-to-r from-danger/80 to-danger' :
                  localWf.status === 'completed' ? 'bg-gradient-to-r from-success/80 to-success' :
                  'bg-gradient-to-r from-blue-400 to-blue-500'
                }`}
                style={{ width: `${Math.round(((completedCount + failedCount) / tasks.length) * 100)}%` }}
              />
            </div>
          </CardContent>
        </Card>
      )}

      {/* ── Summary Report ── */}
      {summary && (
        <Card className="border-accent/30 bg-gradient-to-r from-accent/5 to-transparent">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-accent" />
              Analysis Summary
              <Badge variant={
                summary.rating_color === 'green' ? 'success' :
                summary.rating_color === 'yellow' ? 'default' :
                'destructive'
              } className="ml-2">
                {summary.rating}
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center p-3 rounded-xl bg-surface">
                <p className="text-2xl font-bold text-danger">{summary.total_errors}</p>
                <p className="text-xs text-text-muted">Errors</p>
              </div>
              <div className="text-center p-3 rounded-xl bg-surface">
                <p className="text-2xl font-bold text-yellow-400">{summary.total_warnings}</p>
                <p className="text-xs text-text-muted">Warnings</p>
              </div>
              <div className="text-center p-3 rounded-xl bg-surface">
                <p className="text-2xl font-bold text-danger">{summary.total_security_high}</p>
                <p className="text-xs text-text-muted">High Security</p>
              </div>
              <div className="text-center p-3 rounded-xl bg-surface">
                <p className="text-2xl font-bold text-yellow-400">{summary.total_security_medium}</p>
                <p className="text-xs text-text-muted">Medium Security</p>
              </div>
            </div>

            {summary.recommendations?.length > 0 && (
              <div>
                <h4 className="text-sm font-semibold mb-2 flex items-center gap-2"><Lightbulb className="h-4 w-4 text-yellow-400" /> Recommendations</h4>
                <ul className="space-y-1">
                  {summary.recommendations.map((r: string, i: number) => (
                    <li key={i} className="text-sm text-text-muted flex items-start gap-2">
                      <CheckCircle className="h-4 w-4 text-success shrink-0 mt-0.5" />
                      {r}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {summary.follow_ups?.length > 0 && (
              <div>
                <h4 className="text-sm font-semibold mb-2">Quick Actions</h4>
                <div className="flex flex-wrap gap-2">
                  {summary.follow_ups.map((fu: any, i: number) => (
                    <Button key={i} variant="outline" size="sm" onClick={() => { setAiQuery(fu.query); handleAskAI(fu.query); }}>
                      <MessageSquare className="mr-1 h-3 w-3" /> {fu.action}
                    </Button>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* ── AI Chat ── */}
      {localWf.status === 'completed' && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <MessageSquare className="h-5 w-5 text-accent" />
              Ask AI About Results
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex gap-2">
              <input
                value={aiQuery}
                onChange={e => setAiQuery(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter' && aiQuery.trim()) handleAskAI(aiQuery); }}
                placeholder="e.g., How do I fix the security issues? Show me code examples."
                className="flex-1 px-3 py-2 rounded-lg bg-surface border border-border text-text text-sm focus:outline-none focus:border-accent"
              />
              <Button onClick={() => handleAskAI(aiQuery)} disabled={aiLoading || !aiQuery.trim()}>
                {aiLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
              </Button>
            </div>
            {aiResponse && (
              <div className="rounded-lg bg-surface p-4 text-sm text-text-muted whitespace-pre-wrap border border-border max-h-96 overflow-y-auto">
                {aiResponse}
              </div>
            )}
            <div className="flex flex-wrap gap-2">
              <Button variant="ghost" size="sm" onClick={() => handleAskAI('Summarize all findings in simple terms')}>Summarize</Button>
              <Button variant="ghost" size="sm" onClick={() => handleAskAI('What are the top 3 things I should fix first?')}>Top 3 fixes</Button>
              <Button variant="ghost" size="sm" onClick={() => handleAskAI('Generate a GitHub issue for each critical error')}>Generate issues</Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* ── Visual Pipeline ── */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-accent" />
            Pipeline Execution
          </CardTitle>
        </CardHeader>
        <CardContent>
          {tasks.length > 0 ? (
            <div className="space-y-0">
              {tasks.map((task: any, i: number) => {
                const isLast = i === tasks.length - 1;
                const sc = getStepConfig(task.status);
                const StepIcon = STEP_ICONS[i % STEP_ICONS.length];
                const isExpanded = expandedTasks.has(i);

                return (
                  <div key={task.id || i} className="flex group/step">
                    {/* ── Stepper ── */}
                    <div className="flex flex-col items-center mr-5">
                      <div className={`relative flex items-center justify-center w-14 h-14 rounded-2xl border-2 shrink-0 z-10 transition-all duration-300 ${sc.ring}`}>
                        {task.status === 'completed' && <CheckCircle2 className="h-6 w-6 text-success" />}
                        {task.status === 'failed' && <XCircle className="h-6 w-6 text-danger" />}
                        {task.status === 'running' && <Loader2 className="h-6 w-6 text-blue-400 animate-spin" />}
                        {task.status === 'pending' && (
                          <StepIcon className="h-6 w-6 text-text-muted group-hover/step:text-accent transition-colors" />
                        )}
                        <span className={`absolute -top-2 -right-2 w-6 h-6 rounded-full text-[11px] font-bold flex items-center justify-center ${
                          task.status === 'completed' ? 'bg-success text-white' :
                          task.status === 'failed' ? 'bg-danger text-white' :
                          task.status === 'running' ? 'bg-blue-500 text-white animate-pulse' :
                          'bg-surface-hover text-text-muted border border-border'
                        }`}>
                          {i + 1}
                        </span>
                      </div>
                      {!isLast && (
                        <div className={`w-0.5 flex-1 min-h-[3rem] transition-all duration-500 ${sc.line}`} />
                      )}
                    </div>

                    {/* ── Content ── */}
                    <div className={`flex-1 ${isLast ? '' : 'pb-6'}`}>
                      <div className={`rounded-xl border p-5 transition-all duration-300 ${
                        task.status === 'running' ? 'border-blue-500/40 bg-blue-500/5 shadow-lg shadow-blue-500/10' :
                        task.status === 'completed' ? 'border-success/30 bg-success/5' :
                        task.status === 'failed' ? 'border-danger/30 bg-danger/5' :
                        'border-border bg-surface/50 hover:bg-surface-hover/50 hover:border-text-muted/30'
                      }`}>
                        <div className="flex items-center justify-between cursor-pointer" onClick={() => task.result && toggleTask(i)}>
                          <div className="flex-1">
                            <div className="flex items-center gap-3">
                              <p className={`text-base font-semibold ${
                                task.status === 'completed' ? 'text-success' :
                                task.status === 'failed' ? 'text-danger' :
                                task.status === 'running' ? 'text-blue-400' :
                                'text-text'
                              }`}>
                                {task.title}
                              </p>
                              {task.priority && task.priority !== 'medium' && (
                                <Badge variant={task.priority === 'high' || task.priority === 'critical' ? 'destructive' : 'secondary'} className="text-xs">
                                  {task.priority}
                                </Badge>
                              )}
                            </div>
                            {task.description && <p className="text-sm text-text-muted mt-1">{task.description}</p>}
                          </div>
                          <div className="flex items-center gap-3 ml-4">
                            {task.duration != null && (
                              <span className="text-sm font-mono text-text-muted flex items-center gap-1">
                                <Timer className="h-3.5 w-3.5" />{task.duration}s
                              </span>
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

                        {task.result && isExpanded && (
                          <div className="mt-4 space-y-3">
                            <TaskResult content={task.result} status={task.status} />
                            {task.status === 'completed' && (
                              <div className="flex gap-2">
                                <Button variant="ghost" size="sm" onClick={(e) => { e.stopPropagation(); handleAskAI(`Explain the results of "${task.title}" and how to fix the issues found`); }}>
                                  <MessageSquare className="mr-1 h-3 w-3" /> Ask AI
                                </Button>
                              </div>
                            )}
                          </div>
                        )}

                        {task.result && !isExpanded && (
                          <div className="mt-2 text-xs text-text-muted truncate">{task.result.split('\n')[0]}</div>
                        )}

                        {task.status === 'running' && (
                          <div className="mt-3 flex items-center gap-2 text-sm text-blue-400">
                            <Loader2 className="h-4 w-4 animate-spin" />
                            <span>Executing step {i + 1}...</span>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <p className="text-center text-text-muted py-12">No tasks in this workflow.</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
