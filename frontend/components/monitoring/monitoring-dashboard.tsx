'use client';

import { useEffect, useState, useCallback, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useMonitoringStore } from '@/stores/monitoring-store';
import type {
  OverviewData,
  AgentSnapshot,
  WorkflowSnapshot,
  ToolSnapshot,
  MemoryStatus,
  ComponentHealth,
  EventSeverity,
  TimelineEventType,
  ComponentStatus,
  TrendData,
  DailyActivity,
} from '@/types/monitoring';
import {
  Activity,
  RefreshCw,
  Users,
  Workflow,
  Wrench,
  Database,
  Clock,
  CheckCircle,
  XCircle,
  AlertTriangle,
  BarChart3,
  Heart,
  Filter,
  ArrowUpRight,
  ArrowDownRight,
  Minus,
  Zap,
  Server,
  Brain,
  Search,
  Shield,
  FileText,
  PlayCircle,
  PauseCircle,
  TrendingUp,
  TrendingDown,
  Calendar,
  Loader2,
} from 'lucide-react';

const REFRESH_INTERVAL = 30000;

function getHealthColor(status: ComponentHealth): string {
  switch (status) {
    case 'healthy':
      return 'text-green-500';
    case 'degraded':
      return 'text-yellow-500';
    case 'unhealthy':
      return 'text-red-500';
    case 'unknown':
      return 'text-text-muted';
    default:
      return 'text-text-muted';
  }
}

function getHealthBg(status: ComponentHealth): string {
  switch (status) {
    case 'healthy':
      return 'bg-green-500/10 border-green-500/20';
    case 'degraded':
      return 'bg-yellow-500/10 border-yellow-500/20';
    case 'unhealthy':
      return 'bg-red-500/10 border-red-500/20';
    case 'unknown':
      return 'bg-surface-hover border-border';
    default:
      return 'bg-surface-hover border-border';
  }
}

function getHealthBadgeVariant(status: ComponentHealth): 'success' | 'warning' | 'destructive' | 'secondary' {
  switch (status) {
    case 'healthy':
      return 'success';
    case 'degraded':
      return 'warning';
    case 'unhealthy':
      return 'destructive';
    case 'unknown':
    default:
      return 'secondary';
  }
}

function getStatusBadgeVariant(status: string): 'success' | 'warning' | 'destructive' | 'secondary' {
  const s = status.toLowerCase();
  if (s === 'healthy' || s === 'completed' || s === 'idle' || s === 'success') return 'success';
  if (s === 'running' || s === 'executing' || s === 'assigned' || s === 'degraded') return 'warning';
  if (s === 'failed' || s === 'error' || s === 'unhealthy' || s === 'offline') return 'destructive';
  return 'secondary';
}

function getSeverityColor(severity: EventSeverity): string {
  switch (severity) {
    case 'info':
      return 'bg-blue-500/10 border-l-blue-500';
    case 'warning':
      return 'bg-yellow-500/10 border-l-yellow-500';
    case 'error':
      return 'bg-red-500/10 border-l-red-500';
    default:
      return 'bg-surface-hover border-l-border';
  }
}

function formatTimestamp(ts: string | null): string {
  if (!ts) return 'Never';
  const date = new Date(ts);
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

function formatDuration(seconds: number): string {
  if (seconds < 60) return `${Math.round(seconds)}s`;
  const m = Math.floor(seconds / 60);
  const s = Math.round(seconds % 60);
  return `${m}m ${s}s`;
}

function formatLatency(ms: number): string {
  if (ms < 1) return '<1ms';
  if (ms < 1000) return `${Math.round(ms)}ms`;
  return `${(ms / 1000).toFixed(2)}s`;
}

function getEventIcon(type: TimelineEventType) {
  switch (type) {
    case 'workflow_started':
    case 'execution_started':
      return <PlayCircle className="h-4 w-4 text-blue-500" />;
    case 'workflow_completed':
    case 'execution_completed':
    case 'task_completed':
      return <CheckCircle className="h-4 w-4 text-green-500" />;
    case 'workflow_failed':
    case 'task_failed':
      return <XCircle className="h-4 w-4 text-red-500" />;
    case 'task_started':
      return <Clock className="h-4 w-4 text-yellow-500" />;
    case 'agent_assigned':
      return <Users className="h-4 w-4 text-purple-500" />;
    case 'tool_called':
    case 'tool_completed':
      return <Wrench className="h-4 w-4 text-orange-500" />;
    case 'memory_indexed':
    case 'memory_searched':
      return <Database className="h-4 w-4 text-cyan-500" />;
    case 'system_health_check':
      return <Heart className="h-4 w-4 text-pink-500" />;
    case 'approval_requested':
    case 'approval_granted':
      return <Shield className="h-4 w-4 text-indigo-500" />;
    default:
      return <Activity className="h-4 w-4 text-text-muted" />;
  }
}

function formatEventType(type: TimelineEventType): string {
  return type
    .split('_')
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ');
}

interface StatCardProps {
  icon: React.ReactNode;
  label: string;
  value: number | string;
  subtitle?: string;
  color?: string;
}

function StatCard({ icon, label, value, subtitle, color = 'text-primary' }: StatCardProps) {
  return (
    <Card>
      <CardContent className="p-5">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className={`p-2 rounded-lg bg-surface-hover ${color}`}>
              {icon}
            </div>
            <div>
              <p className="text-sm text-text-muted">{label}</p>
              <p className="text-2xl font-bold text-text">{value}</p>
              {subtitle && (
                <p className="text-xs text-text-muted mt-0.5">{subtitle}</p>
              )}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

interface ProgressBarProps {
  value: number;
  max?: number;
  className?: string;
}

function ProgressBar({ value, max = 100, className = '' }: ProgressBarProps) {
  const percent = Math.min(Math.max((value / max) * 100, 0), 100);
  let barColor = 'bg-green-500';
  if (percent < 30) barColor = 'bg-red-500';
  else if (percent < 70) barColor = 'bg-yellow-500';

  return (
    <div className={`w-full h-2 bg-surface-hover rounded-full overflow-hidden ${className}`}>
      <div
        className={`h-full rounded-full transition-all duration-500 ${barColor}`}
        style={{ width: `${percent}%` }}
      />
    </div>
  );
}

interface HealthIndicatorProps {
  status: ComponentHealth;
  label?: string;
}

function HealthIndicator({ status, label }: HealthIndicatorProps) {
  const dotColor = {
    healthy: 'bg-green-500',
    degraded: 'bg-yellow-500',
    unhealthy: 'bg-red-500',
    unknown: 'bg-text-muted',
  }[status];

  return (
    <div className="flex items-center space-x-2">
      <span className={`h-2 w-2 rounded-full ${dotColor}`} />
      {label && <span className="text-sm text-text">{label}</span>}
    </div>
  );
}

interface OverviewTabProps {
  overview: OverviewData;
}

function OverviewTab({ overview }: OverviewTabProps) {
  const agents = overview.agents;
  const workflows = overview.workflows;
  const tools = overview.tools;
  const memory = overview.memory;
  const health = overview.health;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={<Users className="h-5 w-5" />}
          label="Agents"
          value={agents.total}
          subtitle={`${agents.running} running · ${agents.idle} idle`}
          color="text-blue-500"
        />
        <StatCard
          icon={<Workflow className="h-5 w-5" />}
          label="Workflows"
          value={workflows.total}
          subtitle={`${workflows.running} running · ${workflows.completed} done`}
          color="text-purple-500"
        />
        <StatCard
          icon={<Wrench className="h-5 w-5" />}
          label="Tools"
          value={tools.total}
          subtitle={`${tools.healthy} healthy · ${tools.avg_latency.toFixed(0)}ms avg`}
          color="text-orange-500"
        />
        <StatCard
          icon={<Database className="h-5 w-5" />}
          label="Memory"
          value={memory.total_chunks.toLocaleString()}
          subtitle={`${memory.total_repositories} repos`}
          color="text-cyan-500"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">System Health</CardTitle>
            <CardDescription>Component status overview</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {health.components.slice(0, 6).map((component) => (
                <div
                  key={component.name}
                  className="flex items-center justify-between p-2.5 rounded-lg border border-border bg-surface-hover"
                >
                  <div className="flex items-center space-x-3">
                    <HealthIndicator status={component.status} />
                    <div>
                      <p className="text-sm font-medium text-text">{component.name}</p>
                      <p className="text-xs text-text-muted">{component.message}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-text-muted">{formatLatency(component.latency_ms)}</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Execution Overview</CardTitle>
            <CardDescription>Current execution pipeline</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 rounded-lg border border-border bg-surface-hover text-center">
                <p className="text-3xl font-bold text-text">{overview.execution.total}</p>
                <p className="text-sm text-text-muted mt-1">Total Executions</p>
              </div>
              <div className="p-4 rounded-lg border border-border bg-surface-hover text-center">
                <p className="text-3xl font-bold text-green-500">{overview.execution.completed}</p>
                <p className="text-sm text-text-muted mt-1">Completed</p>
              </div>
              <div className="p-4 rounded-lg border border-border bg-surface-hover text-center">
                <p className="text-3xl font-bold text-blue-500">{overview.execution.running}</p>
                <p className="text-sm text-text-muted mt-1">Running</p>
              </div>
              <div className="p-4 rounded-lg border border-border bg-surface-hover text-center">
                <p className="text-3xl font-bold text-red-500">{overview.execution.failed}</p>
                <p className="text-sm text-text-muted mt-1">Failed</p>
              </div>
            </div>
            {overview.execution.total > 0 && (
              <div className="mt-4">
                <div className="flex justify-between text-sm mb-1.5">
                  <span className="text-text-muted">Success Rate</span>
                  <span className="font-medium text-text">
                    {overview.execution.total > 0
                      ? ((overview.execution.completed / overview.execution.total) * 100).toFixed(1)
                      : 0}
                    %
                  </span>
                </div>
                <ProgressBar
                  value={overview.execution.completed}
                  max={overview.execution.total}
                />
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Quick Links</CardTitle>
          <CardDescription>Jump to monitoring sections</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {[
              { label: 'Workflows', tab: 'workflows', count: workflows.total, icon: <Workflow className="h-4 w-4" /> },
              { label: 'Agents', tab: 'agents', count: agents.total, icon: <Users className="h-4 w-4" /> },
              { label: 'Tools', tab: 'tools', count: tools.total, icon: <Wrench className="h-4 w-4" /> },
              { label: 'Health', tab: 'health', count: health.components.length, icon: <Heart className="h-4 w-4" /> },
            ].map((item) => (
              <button
                key={item.tab}
                className="flex items-center space-x-3 p-3 rounded-lg border border-border bg-surface-hover hover:bg-surface-active transition-colors text-left"
              >
                <div className="p-2 rounded-md bg-surface text-text-muted">
                  {item.icon}
                </div>
                <div>
                  <p className="text-sm font-medium text-text">{item.label}</p>
                  <p className="text-xs text-text-muted">{item.count} items</p>
                </div>
              </button>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

interface WorkflowsTabProps {
  workflows: WorkflowSnapshot[];
}

function WorkflowsTab({ workflows }: WorkflowsTabProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');

  const filtered = useMemo(() => {
    return workflows.filter((w) => {
      const matchesSearch =
        w.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        w.workflow_id.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesStatus = statusFilter === 'all' || w.status.toLowerCase() === statusFilter;
      return matchesSearch && matchesStatus;
    });
  }, [workflows, searchQuery, statusFilter]);

  const runningCount = workflows.filter((w) => w.status === 'running').length;
  const completedCount = workflows.filter((w) => w.status === 'completed').length;
  const failedCount = workflows.filter((w) => w.status === 'failed').length;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard
          icon={<PlayCircle className="h-5 w-5" />}
          label="Running"
          value={runningCount}
          color="text-blue-500"
        />
        <StatCard
          icon={<CheckCircle className="h-5 w-5" />}
          label="Completed"
          value={completedCount}
          color="text-green-500"
        />
        <StatCard
          icon={<XCircle className="h-5 w-5" />}
          label="Failed"
          value={failedCount}
          color="text-red-500"
        />
      </div>

      <div className="flex flex-col sm:flex-row gap-3">
        <div className="flex-1">
          <Input
            placeholder="Search workflows..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        <div className="relative">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="h-10 rounded-md border border-border bg-surface px-3 py-2 text-sm text-text appearance-none pr-10 focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
          >
            <option value="all">All Statuses</option>
            <option value="running">Running</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
            <option value="pending">Pending</option>
          </select>
          <Filter className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-muted pointer-events-none" />
        </div>
      </div>

      <div className="space-y-3">
        {filtered.length === 0 ? (
          <Card>
            <CardContent className="p-8 text-center">
              <Workflow className="h-12 w-12 text-text-muted mx-auto mb-3" />
              <p className="text-text-muted">No workflows found</p>
            </CardContent>
          </Card>
        ) : (
          filtered.map((workflow) => (
            <Card key={workflow.workflow_id}>
              <CardContent className="p-5">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1 min-w-0">
                    <h3 className="text-sm font-semibold text-text truncate">
                      {workflow.title}
                    </h3>
                    <p className="text-xs text-text-muted mt-0.5 font-mono">
                      {workflow.workflow_id.slice(0, 12)}...
                    </p>
                  </div>
                  <div className="flex items-center space-x-2 ml-3">
                    {workflow.risk_level && (
                      <Badge
                        variant={
                          workflow.risk_level === 'high'
                            ? 'destructive'
                            : workflow.risk_level === 'medium'
                            ? 'warning'
                            : 'secondary'
                        }
                        className="text-xs"
                      >
                        {workflow.risk_level}
                      </Badge>
                    )}
                    <Badge variant={getStatusBadgeVariant(workflow.status)}>
                      {workflow.status}
                    </Badge>
                  </div>
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between text-xs">
                    <span className="text-text-muted">
                      Tasks: {workflow.tasks_completed}/{workflow.tasks_total}
                      {workflow.tasks_failed > 0 && (
                        <span className="text-red-500 ml-1">({workflow.tasks_failed} failed)</span>
                      )}
                    </span>
                    <span className="text-text-muted">{formatDuration(workflow.elapsed_time)}</span>
                  </div>
                  <ProgressBar value={workflow.progress} />
                  <p className="text-xs text-text-muted text-right">{workflow.progress.toFixed(1)}%</p>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}

interface AgentsTabProps {
  agents: AgentSnapshot[];
}

function AgentsTab({ agents }: AgentsTabProps) {
  const [searchQuery, setSearchQuery] = useState('');

  const filtered = useMemo(() => {
    return agents.filter(
      (a) =>
        a.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        a.agent_type.toLowerCase().includes(searchQuery.toLowerCase())
    );
  }, [agents, searchQuery]);

  const healthyCount = agents.filter((a) => a.status === 'idle' || a.status === 'executing').length;
  const offlineCount = agents.filter((a) => a.status === 'offline').length;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard
          icon={<CheckCircle className="h-5 w-5" />}
          label="Active"
          value={healthyCount}
          color="text-green-500"
        />
        <StatCard
          icon={<Users className="h-5 w-5" />}
          label="Total"
          value={agents.length}
          color="text-blue-500"
        />
        <StatCard
          icon={<XCircle className="h-5 w-5" />}
          label="Offline"
          value={offlineCount}
          color="text-red-500"
        />
      </div>

      <Input
        placeholder="Search agents..."
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
      />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {filtered.length === 0 ? (
          <Card className="md:col-span-2">
            <CardContent className="p-8 text-center">
              <Users className="h-12 w-12 text-text-muted mx-auto mb-3" />
              <p className="text-text-muted">No agents found</p>
            </CardContent>
          </Card>
        ) : (
          filtered.map((agent) => (
            <Card key={agent.agent_id}>
              <CardContent className="p-5">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    <div className={`p-2 rounded-lg ${
                      agent.status === 'executing'
                        ? 'bg-blue-500/10 text-blue-500'
                        : agent.status === 'idle'
                        ? 'bg-green-500/10 text-green-500'
                        : 'bg-surface-hover text-text-muted'
                    }`}>
                      <Brain className="h-5 w-5" />
                    </div>
                    <div>
                      <h3 className="text-sm font-semibold text-text">{agent.name}</h3>
                      <p className="text-xs text-text-muted">{agent.agent_type}</p>
                    </div>
                  </div>
                  <Badge variant={getStatusBadgeVariant(agent.status)}>
                    {agent.status}
                  </Badge>
                </div>

                {agent.current_task_id && (
                  <div className="mb-4 p-2 rounded bg-blue-500/5 border border-blue-500/10">
                    <p className="text-xs text-blue-500">Current Task</p>
                    <p className="text-xs text-text-muted font-mono mt-0.5">
                      {agent.current_task_id.slice(0, 16)}...
                    </p>
                  </div>
                )}

                <div className="grid grid-cols-3 gap-3">
                  <div className="text-center p-2 rounded bg-surface-hover">
                    <p className="text-lg font-bold text-text">{agent.tasks_completed}</p>
                    <p className="text-xs text-text-muted">Completed</p>
                  </div>
                  <div className="text-center p-2 rounded bg-surface-hover">
                    <p className="text-lg font-bold text-red-500">{agent.tasks_failed}</p>
                    <p className="text-xs text-text-muted">Failed</p>
                  </div>
                  <div className="text-center p-2 rounded bg-surface-hover">
                    <p className="text-lg font-bold text-text">{formatLatency(agent.avg_execution_time * 1000)}</p>
                    <p className="text-xs text-text-muted">Avg Time</p>
                  </div>
                </div>

                {agent.last_active && (
                  <p className="text-xs text-text-muted mt-3">
                    Last active: {formatTimestamp(agent.last_active)}
                  </p>
                )}
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}

interface ToolsTabProps {
  tools: ToolSnapshot[];
}

function ToolsTab({ tools }: ToolsTabProps) {
  const [searchQuery, setSearchQuery] = useState('');

  const filtered = useMemo(() => {
    return tools.filter(
      (t) =>
        t.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        t.provider.toLowerCase().includes(searchQuery.toLowerCase())
    );
  }, [tools, searchQuery]);

  const totalCalls = tools.reduce((sum, t) => sum + t.total_calls, 0);
  const totalErrors = tools.reduce((sum, t) => sum + t.error_count, 0);
  const avgLatency =
    tools.length > 0
      ? tools.reduce((sum, t) => sum + t.avg_latency, 0) / tools.length
      : 0;
  const healthyTools = tools.filter((t) => t.health_status === 'healthy').length;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={<Wrench className="h-5 w-5" />}
          label="Total Calls"
          value={totalCalls.toLocaleString()}
          color="text-orange-500"
        />
        <StatCard
          icon={<CheckCircle className="h-5 w-5" />}
          label="Healthy"
          value={`${healthyTools}/${tools.length}`}
          color="text-green-500"
        />
        <StatCard
          icon={<XCircle className="h-5 w-5" />}
          label="Errors"
          value={totalErrors.toLocaleString()}
          color="text-red-500"
        />
        <StatCard
          icon={<Clock className="h-5 w-5" />}
          label="Avg Latency"
          value={formatLatency(avgLatency)}
          color="text-blue-500"
        />
      </div>

      <Input
        placeholder="Search tools..."
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
      />

      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left px-4 py-3 text-xs font-medium text-text-muted uppercase tracking-wider">Tool</th>
                  <th className="text-left px-4 py-3 text-xs font-medium text-text-muted uppercase tracking-wider">Provider</th>
                  <th className="text-right px-4 py-3 text-xs font-medium text-text-muted uppercase tracking-wider">Calls</th>
                  <th className="text-right px-4 py-3 text-xs font-medium text-text-muted uppercase tracking-wider">Success</th>
                  <th className="text-right px-4 py-3 text-xs font-medium text-text-muted uppercase tracking-wider">Errors</th>
                  <th className="text-right px-4 py-3 text-xs font-medium text-text-muted uppercase tracking-wider">Latency</th>
                  <th className="text-center px-4 py-3 text-xs font-medium text-text-muted uppercase tracking-wider">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {filtered.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="px-4 py-12 text-center text-text-muted">
                      No tools found
                    </td>
                  </tr>
                ) : (
                  filtered.map((tool) => {
                    const errorRate =
                      tool.total_calls > 0
                        ? ((tool.error_count / tool.total_calls) * 100).toFixed(1)
                        : '0.0';
                    return (
                      <tr key={tool.tool_id} className="hover:bg-surface-hover transition-colors">
                        <td className="px-4 py-3">
                          <div className="flex items-center space-x-2">
                            <Wrench className="h-4 w-4 text-text-muted" />
                            <span className="text-sm font-medium text-text">{tool.name}</span>
                          </div>
                        </td>
                        <td className="px-4 py-3 text-sm text-text-muted">{tool.provider}</td>
                        <td className="px-4 py-3 text-sm text-text text-right font-mono">{tool.total_calls.toLocaleString()}</td>
                        <td className="px-4 py-3 text-sm text-green-500 text-right font-mono">{tool.success_count.toLocaleString()}</td>
                        <td className="px-4 py-3 text-sm text-right font-mono">
                          <span className={tool.error_count > 0 ? 'text-red-500' : 'text-text-muted'}>
                            {tool.error_count.toLocaleString()} ({errorRate}%)
                          </span>
                        </td>
                        <td className="px-4 py-3 text-sm text-text text-right font-mono">{formatLatency(tool.avg_latency)}</td>
                        <td className="px-4 py-3 text-center">
                          <Badge variant={getStatusBadgeVariant(tool.health_status)}>
                            {tool.health_status}
                          </Badge>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

interface MemoryTabProps {
  memory: MemoryStatus;
}

function MemoryTab({ memory }: MemoryTabProps) {
  const stats = [
    { label: 'Total Chunks', value: memory.total_chunks.toLocaleString(), icon: <Database className="h-4 w-4" /> },
    { label: 'Repositories', value: memory.total_repositories, icon: <FileText className="h-4 w-4" /> },
    { label: 'Collections', value: memory.collections, icon: <Search className="h-4 w-4" /> },
    { label: 'Total Searches', value: memory.total_searches.toLocaleString(), icon: <Search className="h-4 w-4" /> },
  ];

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat) => (
          <Card key={stat.label}>
            <CardContent className="p-5">
              <div className="flex items-center space-x-3">
                <div className="p-2 rounded-lg bg-surface-hover text-cyan-500">
                  {stat.icon}
                </div>
                <div>
                  <p className="text-sm text-text-muted">{stat.label}</p>
                  <p className="text-xl font-bold text-text">{stat.value}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Search Performance</CardTitle>
            <CardDescription>Vector search metrics</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex justify-between items-center p-3 rounded-lg bg-surface-hover">
              <span className="text-sm text-text-muted">Average Search Time</span>
              <span className="text-sm font-medium text-text">{formatLatency(memory.avg_search_time)}</span>
            </div>
            <div className="flex justify-between items-center p-3 rounded-lg bg-surface-hover">
              <span className="text-sm text-text-muted">Total Searches</span>
              <span className="text-sm font-medium text-text">{memory.total_searches.toLocaleString()}</span>
            </div>
            <div className="flex justify-between items-center p-3 rounded-lg bg-surface-hover">
              <span className="text-sm text-text-muted">Embedding Model</span>
              <Badge variant="outline" className="text-xs">{memory.embedding_model}</Badge>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Cache Performance</CardTitle>
            <CardDescription>Cache utilization metrics</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span className="text-text-muted">Cache Hit Rate</span>
                <span className="font-medium text-text">{(memory.cache_hit_rate * 100).toFixed(1)}%</span>
              </div>
              <ProgressBar value={memory.cache_hit_rate * 100} />
              <p className="text-xs text-text-muted mt-1.5">
                {memory.cache_hit_rate >= 0.8
                  ? 'Excellent cache performance'
                  : memory.cache_hit_rate >= 0.5
                  ? 'Moderate cache hit rate'
                  : 'Cache hit rate below target'}
              </p>
            </div>
            <div className="flex justify-between items-center p-3 rounded-lg bg-surface-hover">
              <span className="text-sm text-text-muted">Cache Status</span>
              <Badge
                variant={
                  memory.cache_hit_rate >= 0.8
                    ? 'success'
                    : memory.cache_hit_rate >= 0.5
                    ? 'warning'
                    : 'destructive'
                }
              >
                {memory.cache_hit_rate >= 0.8 ? 'Optimal' : memory.cache_hit_rate >= 0.5 ? 'Moderate' : 'Poor'}
              </Badge>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

interface AnalyticsTabProps {
  analytics: import('@/types/monitoring').AnalyticsData;
}

function AnalyticsTab({ analytics }: AnalyticsTabProps) {
  const [timeRange, setTimeRange] = useState('7d');
  const { fetchAnalytics } = useMonitoringStore();

  useEffect(() => {
    fetchAnalytics(timeRange);
  }, [timeRange, fetchAnalytics]);

  const maxActivity = useMemo(() => {
    if (analytics.daily_activity.length === 0) return 1;
    return Math.max(
      ...analytics.daily_activity.map((d) =>
        Math.max(d.workflows_started, d.workflows_completed, d.tasks_completed, d.tools_used)
      ),
      1
    );
  }, [analytics.daily_activity]);

  const renderTrend = (trend: TrendData) => {
    const Icon =
      trend.direction === 'up'
        ? TrendingUp
        : trend.direction === 'down'
        ? TrendingDown
        : Minus;
    const color =
      trend.direction === 'up'
        ? 'text-green-500'
        : trend.direction === 'down'
        ? 'text-red-500'
        : 'text-text-muted';

    return (
      <div className="flex items-center space-x-2">
        <Icon className={`h-4 w-4 ${color}`} />
        <span className={`text-sm font-medium ${color}`}>
          {trend.change_percent > 0 ? '+' : ''}
          {trend.change_percent.toFixed(1)}%
        </span>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-text">Analytics</h3>
          <p className="text-sm text-text-muted">Performance trends and activity insights</p>
        </div>
        <div className="relative">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="h-10 rounded-md border border-border bg-surface px-3 py-2 text-sm text-text appearance-none pr-10 focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
          >
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
          </select>
          <Calendar className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-muted pointer-events-none" />
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-text-muted">Workflows Started</p>
                <p className="text-2xl font-bold text-text">
                  {analytics.daily_activity.reduce((s, d) => s + d.workflows_started, 0)}
                </p>
              </div>
              <Workflow className="h-5 w-5 text-purple-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-text-muted">Tasks Completed</p>
                <p className="text-2xl font-bold text-text">
                  {analytics.daily_activity.reduce((s, d) => s + d.tasks_completed, 0)}
                </p>
              </div>
              <CheckCircle className="h-5 w-5 text-green-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-text-muted">Execution Trend</p>
                {renderTrend(analytics.execution_trend)}
              </div>
              <BarChart3 className="h-5 w-5 text-blue-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-text-muted">Success Trend</p>
                {renderTrend(analytics.success_trend)}
              </div>
              <TrendingUp className="h-5 w-5 text-green-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Daily Activity</CardTitle>
          <CardDescription>Workflows and tasks over time</CardDescription>
        </CardHeader>
        <CardContent>
          {analytics.daily_activity.length === 0 ? (
            <div className="text-center py-8">
              <BarChart3 className="h-12 w-12 text-text-muted mx-auto mb-3" />
              <p className="text-text-muted">No activity data available</p>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="flex items-end space-x-1 h-40">
                {analytics.daily_activity.map((day, i) => {
                  const height = (day.tasks_completed / maxActivity) * 100;
                  return (
                    <div
                      key={i}
                      className="flex-1 flex flex-col items-center justify-end group relative"
                    >
                      <div
                        className="w-full bg-primary/80 rounded-t-sm transition-all hover:bg-primary min-h-[2px]"
                        style={{ height: `${Math.max(height, 2)}%` }}
                      />
                      <div className="absolute -top-20 left-1/2 -translate-x-1/2 bg-surface border border-border rounded-md px-2 py-1 text-xs text-text opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-10">
                        <div>{day.period}</div>
                        <div className="text-text-muted">Started: {day.workflows_started}</div>
                        <div className="text-text-muted">Completed: {day.workflows_completed}</div>
                        <div className="text-text-muted">Tasks: {day.tasks_completed}</div>
                        <div className="text-text-muted">Tools: {day.tools_used}</div>
                      </div>
                    </div>
                  );
                })}
              </div>
              <div className="flex justify-between text-xs text-text-muted px-1">
                <span>{analytics.daily_activity[0]?.period}</span>
                <span>{analytics.daily_activity[analytics.daily_activity.length - 1]?.period}</span>
              </div>
              <div className="flex items-center space-x-4 text-xs text-text-muted">
                <div className="flex items-center space-x-1.5">
                  <span className="h-2.5 w-2.5 rounded-sm bg-primary/80" />
                  <span>Tasks Completed</span>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Most Active Agent</CardTitle>
          </CardHeader>
          <CardContent>
            {analytics.most_active_agent && Object.keys(analytics.most_active_agent).length > 0 ? (
              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 rounded-lg bg-surface-hover">
                  <div className="flex items-center space-x-3">
                    <div className="p-2 rounded-lg bg-blue-500/10">
                      <Brain className="h-5 w-5 text-blue-500" />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-text">
                        {(analytics.most_active_agent as Record<string, unknown>).name as string || 'Unknown'}
                      </p>
                      <p className="text-xs text-text-muted">
                        {(analytics.most_active_agent as Record<string, unknown>).agent_type as string || 'Agent'}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-bold text-text">
                      {(analytics.most_active_agent as Record<string, unknown>).tasks_completed as number || 0}
                    </p>
                    <p className="text-xs text-text-muted">tasks</p>
                  </div>
                </div>
              </div>
            ) : (
              <p className="text-sm text-text-muted text-center py-4">No data available</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Most Used Tool</CardTitle>
          </CardHeader>
          <CardContent>
            {analytics.most_used_tool && Object.keys(analytics.most_used_tool).length > 0 ? (
              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 rounded-lg bg-surface-hover">
                  <div className="flex items-center space-x-3">
                    <div className="p-2 rounded-lg bg-orange-500/10">
                      <Wrench className="h-5 w-5 text-orange-500" />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-text">
                        {(analytics.most_used_tool as Record<string, unknown>).name as string || 'Unknown'}
                      </p>
                      <p className="text-xs text-text-muted">
                        {(analytics.most_used_tool as Record<string, unknown>).provider as string || 'Provider'}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-bold text-text">
                      {(analytics.most_used_tool as Record<string, unknown>).total_calls as number || 0}
                    </p>
                    <p className="text-xs text-text-muted">calls</p>
                  </div>
                </div>
              </div>
            ) : (
              <p className="text-sm text-text-muted text-center py-4">No data available</p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

interface HealthTabProps {
  health: import('@/types/monitoring').HealthSummary;
}

function HealthTab({ health }: HealthTabProps) {
  const statusCounts = useMemo(() => {
    const counts = { healthy: 0, degraded: 0, unhealthy: 0, unknown: 0 };
    health.components.forEach((c) => {
      counts[c.status] = (counts[c.status] || 0) + 1;
    });
    return counts;
  }, [health.components]);

  return (
    <div className="space-y-6">
      <Card>
        <CardContent className="p-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <HealthIndicator status={health.overall} />
              <div>
                <h3 className="text-lg font-semibold text-text">Overall Status</h3>
                <p className="text-sm text-text-muted">
                  Last checked: {formatTimestamp(health.checked_at)}
                </p>
              </div>
            </div>
            <Badge variant={getHealthBadgeVariant(health.overall)} className="text-sm px-3 py-1">
              {health.overall.toUpperCase()}
            </Badge>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-bold text-green-500">{statusCounts.healthy}</p>
            <p className="text-sm text-text-muted">Healthy</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-bold text-yellow-500">{statusCounts.degraded}</p>
            <p className="text-sm text-text-muted">Degraded</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-bold text-red-500">{statusCounts.unhealthy}</p>
            <p className="text-sm text-text-muted">Unhealthy</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-bold text-text-muted">{statusCounts.unknown}</p>
            <p className="text-sm text-text-muted">Unknown</p>
          </CardContent>
        </Card>
      </div>

      <div className="space-y-3">
        {health.components.map((component) => (
          <Card key={component.name}>
            <CardContent className="p-5">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4 flex-1 min-w-0">
                  <div className={`p-2 rounded-lg border ${getHealthBg(component.status)}`}>
                    <Server className={`h-5 w-5 ${getHealthColor(component.status)}`} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-2">
                      <h4 className="text-sm font-semibold text-text">{component.name}</h4>
                      <Badge variant={getHealthBadgeVariant(component.status)} className="text-xs">
                        {component.status}
                      </Badge>
                    </div>
                    <p className="text-xs text-text-muted mt-0.5">{component.message}</p>
                  </div>
                </div>
                <div className="flex items-center space-x-6 ml-4">
                  <div className="text-right">
                    <p className="text-sm font-medium text-text">{formatLatency(component.latency_ms)}</p>
                    <p className="text-xs text-text-muted">latency</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-text-muted">{formatTimestamp(component.last_checked)}</p>
                    <p className="text-xs text-text-muted">last checked</p>
                  </div>
                  {component.version && (
                    <div className="text-right">
                      <p className="text-sm text-text-muted font-mono">{component.version}</p>
                      <p className="text-xs text-text-muted">version</p>
                    </div>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

interface TimelineTabProps {
  timeline: import('@/types/monitoring').TimelineEvent[];
  onFilterChange: (params: { hours?: number; event_type?: string; source?: string }) => void;
}

function TimelineTab({ timeline, onFilterChange }: TimelineTabProps) {
  const [hours, setHours] = useState('24');
  const [typeFilter, setTypeFilter] = useState('all');
  const [sourceFilter, setSourceFilter] = useState('');

  const eventTypes: TimelineEventType[] = [
    'workflow_started',
    'workflow_completed',
    'workflow_failed',
    'task_started',
    'task_completed',
    'task_failed',
    'agent_assigned',
    'tool_called',
    'tool_completed',
    'memory_indexed',
    'memory_searched',
    'system_health_check',
    'approval_requested',
    'approval_granted',
  ];

  const sources = useMemo(() => {
    const sourceSet = new Set(timeline.map((e) => e.source));
    return Array.from(sourceSet).sort();
  }, [timeline]);

  const filtered = useMemo(() => {
    return timeline.filter((e) => {
      const matchesType = typeFilter === 'all' || e.event_type === typeFilter;
      const matchesSource = !sourceFilter || e.source.toLowerCase().includes(sourceFilter.toLowerCase());
      return matchesType && matchesSource;
    });
  }, [timeline, typeFilter, sourceFilter]);

  useEffect(() => {
    const params: { hours?: number; event_type?: string; source?: string } = {};
    if (hours !== 'all') params.hours = parseInt(hours, 10);
    if (typeFilter !== 'all') params.event_type = typeFilter;
    if (sourceFilter) params.source = sourceFilter;
    onFilterChange(params);
  }, [hours, typeFilter, sourceFilter, onFilterChange]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative">
          <select
            value={hours}
            onChange={(e) => setHours(e.target.value)}
            className="h-10 rounded-md border border-border bg-surface px-3 py-2 text-sm text-text appearance-none pr-10 focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
          >
            <option value="1">Last 1 Hour</option>
            <option value="6">Last 6 Hours</option>
            <option value="24">Last 24 Hours</option>
            <option value="72">Last 3 Days</option>
            <option value="168">Last 7 Days</option>
            <option value="all">All Time</option>
          </select>
          <Clock className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-muted pointer-events-none" />
        </div>
        <div className="relative">
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="h-10 rounded-md border border-border bg-surface px-3 py-2 text-sm text-text appearance-none pr-10 focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
          >
            <option value="all">All Types</option>
            {eventTypes.map((type) => (
              <option key={type} value={type}>
                {formatEventType(type)}
              </option>
            ))}
          </select>
          <Filter className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-muted pointer-events-none" />
        </div>
        <div className="flex-1">
          <Input
            placeholder="Filter by source..."
            value={sourceFilter}
            onChange={(e) => setSourceFilter(e.target.value)}
          />
        </div>
      </div>

      <div className="text-sm text-text-muted">
        {filtered.length} event{filtered.length !== 1 ? 's' : ''} found
      </div>

      <div className="space-y-2">
        {filtered.length === 0 ? (
          <Card>
            <CardContent className="p-8 text-center">
              <Activity className="h-12 w-12 text-text-muted mx-auto mb-3" />
              <p className="text-text-muted">No events found matching your filters</p>
            </CardContent>
          </Card>
        ) : (
          filtered.map((event) => (
            <div
              key={event.id}
              className={`border-l-4 rounded-r-lg p-4 bg-surface-hover ${getSeverityColor(event.severity)}`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-3">
                  <div className="mt-0.5">{getEventIcon(event.event_type)}</div>
                  <div>
                    <h4 className="text-sm font-medium text-text">{event.title}</h4>
                    <p className="text-xs text-text-muted mt-0.5">{event.description}</p>
                    <div className="flex items-center space-x-3 mt-2">
                      <Badge variant="outline" className="text-xs">
                        {formatEventType(event.event_type)}
                      </Badge>
                      <span className="text-xs text-text-muted">{event.source}</span>
                    </div>
                  </div>
                </div>
                <div className="text-right ml-4 flex-shrink-0">
                  <p className="text-xs text-text-muted">{formatTimestamp(event.timestamp)}</p>
                  <Badge
                    variant={
                      event.severity === 'error'
                        ? 'destructive'
                        : event.severity === 'warning'
                        ? 'warning'
                        : 'secondary'
                    }
                    className="text-xs mt-1"
                  >
                    {event.severity}
                  </Badge>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export function MonitoringDashboard() {
  const {
    overview,
    agents,
    workflows,
    tools,
    memory,
    health,
    timeline,
    analytics,
    isLoading,
    error,
    lastRefresh,
    fetchOverview,
    fetchAgents,
    fetchWorkflows,
    fetchTools,
    fetchMemory,
    fetchHealth,
    fetchTimeline,
    fetchAnalytics,
    refreshAll,
    clearError,
  } = useMonitoringStore();

  const [activeTab, setActiveTab] = useState('overview');
  const [timelineParams, setTimelineParams] = useState<{
    hours?: number;
    event_type?: string;
    source?: string;
  }>({});

  const handleRefresh = useCallback(async () => {
    await refreshAll();
    try { await fetchAnalytics(); } catch {}
    try { await fetchTimeline(timelineParams); } catch {}
  }, [refreshAll, fetchAnalytics, fetchTimeline, timelineParams]);

  const handleTimelineFilter = useCallback(
    (params: { hours?: number; event_type?: string; source?: string }) => {
      setTimelineParams(params);
      fetchTimeline(params);
    },
    [fetchTimeline]
  );

  useEffect(() => {
    handleRefresh();
  }, []);

  useEffect(() => {
    const interval = setInterval(() => {
      handleRefresh();
    }, REFRESH_INTERVAL);
    return () => clearInterval(interval);
  }, [handleRefresh]);

  useEffect(() => {
    if (!overview) return;
    switch (activeTab) {
      case 'agents':
        fetchAgents();
        break;
      case 'workflows':
        fetchWorkflows();
        break;
      case 'tools':
        fetchTools();
        break;
      case 'memory':
        fetchMemory();
        break;
      case 'health':
        fetchHealth();
        break;
      case 'analytics':
        fetchAnalytics();
        break;
      case 'timeline':
        fetchTimeline(timelineParams);
        break;
    }
  }, [activeTab]);

  const isRefreshing = isLoading && lastRefresh !== null;

  return (
    <div className="min-h-screen bg-bg">
      <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-8 gap-4">
          <div>
            <h1 className="text-3xl font-bold text-text">Monitoring Dashboard</h1>
            <div className="flex items-center space-x-2 mt-1">
              <Clock className="h-4 w-4 text-text-muted" />
              <p className="text-sm text-text-muted">
                Last refreshed: {lastRefresh ? formatTimestamp(lastRefresh) : 'Never'}
              </p>
              {isRefreshing && (
                <Loader2 className="h-4 w-4 text-primary animate-spin" />
              )}
            </div>
          </div>
          <div className="flex items-center space-x-3">
            {error && (
              <Button variant="ghost" size="sm" onClick={clearError}>
                <XCircle className="h-4 w-4 mr-1" />
                Dismiss Error
              </Button>
            )}
            <Button
              variant="secondary"
              size="sm"
              onClick={handleRefresh}
              disabled={isLoading}
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </div>
        </div>

        {error && (
          <div className="mb-6 p-4 rounded-lg bg-red-500/10 border border-red-500/20 flex items-center space-x-3">
            <AlertTriangle className="h-5 w-5 text-red-500 flex-shrink-0" />
            <div className="flex-1">
              <p className="text-sm text-red-500 font-medium">Error Loading Data</p>
              <p className="text-xs text-red-500/80">{error}</p>
            </div>
            <Button variant="ghost" size="sm" onClick={clearError}>
              <XCircle className="h-4 w-4" />
            </Button>
          </div>
        )}

        {isLoading && !overview ? (
          <div className="flex flex-col items-center justify-center py-20">
            <Loader2 className="h-12 w-12 text-primary animate-spin mb-4" />
            <p className="text-text-muted">Loading monitoring data...</p>
          </div>
        ) : (
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <div className="mb-6 overflow-x-auto">
              <TabsList className="inline-flex w-full sm:w-auto">
                <TabsTrigger value="overview" className="flex items-center space-x-1.5">
                  <Activity className="h-4 w-4" />
                  <span>Overview</span>
                </TabsTrigger>
                <TabsTrigger value="workflows" className="flex items-center space-x-1.5">
                  <Workflow className="h-4 w-4" />
                  <span>Workflows</span>
                </TabsTrigger>
                <TabsTrigger value="agents" className="flex items-center space-x-1.5">
                  <Users className="h-4 w-4" />
                  <span>Agents</span>
                </TabsTrigger>
                <TabsTrigger value="tools" className="flex items-center space-x-1.5">
                  <Wrench className="h-4 w-4" />
                  <span>Tools</span>
                </TabsTrigger>
                <TabsTrigger value="memory" className="flex items-center space-x-1.5">
                  <Database className="h-4 w-4" />
                  <span>Memory</span>
                </TabsTrigger>
                <TabsTrigger value="analytics" className="flex items-center space-x-1.5">
                  <BarChart3 className="h-4 w-4" />
                  <span>Analytics</span>
                </TabsTrigger>
                <TabsTrigger value="health" className="flex items-center space-x-1.5">
                  <Heart className="h-4 w-4" />
                  <span>Health</span>
                </TabsTrigger>
                <TabsTrigger value="timeline" className="flex items-center space-x-1.5">
                  <Clock className="h-4 w-4" />
                  <span>Timeline</span>
                </TabsTrigger>
              </TabsList>
            </div>

            <TabsContent value="overview">
              {overview && <OverviewTab overview={overview} />}
            </TabsContent>
            <TabsContent value="workflows">
              <WorkflowsTab workflows={workflows} />
            </TabsContent>
            <TabsContent value="agents">
              <AgentsTab agents={agents} />
            </TabsContent>
            <TabsContent value="tools">
              <ToolsTab tools={tools} />
            </TabsContent>
            <TabsContent value="memory">
              {memory && <MemoryTab memory={memory} />}
            </TabsContent>
            <TabsContent value="analytics">
              {analytics && <AnalyticsTab analytics={analytics} />}
            </TabsContent>
            <TabsContent value="health">
              {health && <HealthTab health={health} />}
            </TabsContent>
            <TabsContent value="timeline">
              <TimelineTab
                timeline={timeline}
                onFilterChange={handleTimelineFilter}
              />
            </TabsContent>
          </Tabs>
        )}
      </div>
    </div>
  );
}
