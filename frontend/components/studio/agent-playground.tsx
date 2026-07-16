'use client';

import { useState, useEffect, useCallback } from 'react';
import { useStudioStore } from '@/stores/studio-store';
import { studioService } from '@/services/studio.service';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Skeleton } from '@/components/ui/skeleton';
import { EmptyState } from '@/components/ui/empty-state';
import {
  Bot,
  Play,
  StopCircle,
  CheckCircle,
  XCircle,
  Clock,
  Loader2,
  Settings,
  Save,
  Zap,
  FileCode,
  Wrench,
  BarChart3,
  ChevronRight,
  AlertTriangle,
  RefreshCw,
} from 'lucide-react';
import type { AgentDetail } from '@/types/studio';

type AgentStatus = 'idle' | 'running' | 'error' | 'offline';

interface TestExecution {
  output: string;
  tokensUsed: number;
  latencyMs: number;
  status: 'pending' | 'running' | 'completed' | 'error';
}

interface AgentConfig {
  maxIterations: number;
  timeoutSeconds: number;
  temperature: number;
  promptTemplate: string;
  enabledTools: string[];
}

const STATUS_COLORS: Record<AgentStatus, string> = {
  idle: 'bg-success',
  running: 'bg-info',
  error: 'bg-danger',
  offline: 'bg-text-muted',
};

const STATUS_BADGES: Record<AgentStatus, { label: string; variant: 'success' | 'default' | 'destructive' | 'secondary' }> = {
  idle: { label: 'Idle', variant: 'success' },
  running: { label: 'Running', variant: 'default' },
  error: { label: 'Error', variant: 'destructive' },
  offline: { label: 'Offline', variant: 'secondary' },
};

const MOCK_PROMPT_TEMPLATES = [
  { id: 'default', name: 'Default Assistant' },
  { id: 'coder', name: 'Code Generator' },
  { id: 'reviewer', name: 'Code Reviewer' },
  { id: 'researcher', name: 'Research Analyst' },
];

const MOCK_REPOSITORIES = [
  { id: 'repo-1', name: 'forge-ai/backend' },
  { id: 'repo-2', name: 'forge-ai/frontend' },
  { id: 'repo-3', name: 'forge-ai/docs' },
];

function AgentListPanel({
  agents,
  selectedAgent,
  onSelectAgent,
  isLoading,
}: {
  agents: AgentDetail[];
  selectedAgent: AgentDetail | null;
  onSelectAgent: (agent: AgentDetail) => void;
  isLoading: boolean;
}) {
  const [searchQuery, setSearchQuery] = useState('');

  const filteredAgents = agents.filter(
    (agent) =>
      agent.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      agent.role.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="flex h-full flex-col border-r border-border">
      <div className="border-b border-border p-4">
        <h2 className="mb-3 text-sm font-semibold uppercase text-text-muted">Agents</h2>
        <Input
          placeholder="Search agents..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          leftIcon={<Bot className="h-4 w-4" />}
        />
      </div>
      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="space-y-2 p-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="space-y-2 rounded-lg p-3">
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-3 w-1/2" />
              </div>
            ))}
          </div>
        ) : filteredAgents.length === 0 ? (
          <EmptyState
            icon={<Bot className="h-10 w-10" />}
            title="No agents found"
            description={searchQuery ? 'Try a different search term' : 'No agents available'}
          />
        ) : (
          <div className="space-y-1 p-2">
            {filteredAgents.map((agent) => {
              const status = (agent.status || 'idle') as AgentStatus;
              const isSelected = selectedAgent?.id === agent.id;
              return (
                <button
                  key={agent.id}
                  onClick={() => onSelectAgent(agent)}
                  className={`flex w-full items-start gap-3 rounded-lg p-3 text-left transition-colors ${
                    isSelected
                      ? 'bg-accent/10 border border-accent/30'
                      : 'hover:bg-surface-hover border border-transparent'
                  }`}
                >
                  <div className="mt-1 flex-shrink-0">
                    <div className={`h-2.5 w-2.5 rounded-full ${STATUS_COLORS[status]}`} />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="truncate text-sm font-medium text-text">{agent.name}</span>
                    </div>
                    <p className="truncate text-xs text-text-muted">{agent.role}</p>
                  </div>
                  {isSelected && <ChevronRight className="mt-1 h-4 w-4 flex-shrink-0 text-accent" />}
                </button>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

function AgentDetailsPanel({ agent }: { agent: AgentDetail }) {
  const status = (agent.status || 'idle') as AgentStatus;
  const badge = STATUS_BADGES[status];
  const performance = agent.performance;

  return (
    <div className="flex-1 overflow-y-auto p-6">
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <div className="flex items-start justify-between">
              <div>
                <CardTitle className="text-xl">{agent.name}</CardTitle>
                <CardDescription className="mt-1">{agent.description}</CardDescription>
              </div>
              <Badge variant={badge.variant}>{badge.label}</Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2 text-sm text-text-muted">
              <Zap className="h-4 w-4" />
              <span className="font-medium">Role:</span>
              <span>{agent.role}</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <FileCode className="h-4 w-4" />
              Capabilities
            </CardTitle>
          </CardHeader>
          <CardContent>
            {agent.capabilities.length === 0 ? (
              <p className="text-sm text-text-muted">No capabilities defined</p>
            ) : (
              <div className="flex flex-wrap gap-2">
                {agent.capabilities.map((cap) => (
                  <Badge key={cap} variant="outline" className="text-xs">
                    {cap}
                  </Badge>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Wrench className="h-4 w-4" />
              Assigned Tools
            </CardTitle>
          </CardHeader>
          <CardContent>
            {agent.tools.length === 0 ? (
              <p className="text-sm text-text-muted">No tools assigned</p>
            ) : (
              <div className="space-y-2">
                {agent.tools.map((tool) => (
                  <div
                    key={tool}
                    className="flex items-center gap-2 rounded-md border border-border bg-surface-hover px-3 py-2"
                  >
                    <Wrench className="h-3.5 w-3.5 text-text-muted" />
                    <span className="text-sm text-text">{tool}</span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <BarChart3 className="h-4 w-4" />
              Performance Metrics
            </CardTitle>
          </CardHeader>
          <CardContent>
            {performance ? (
              <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
                <div className="space-y-1">
                  <p className="text-xs font-medium uppercase text-text-muted">Tasks Completed</p>
                  <p className="text-2xl font-bold text-text">{performance.tasks_completed}</p>
                </div>
                <div className="space-y-1">
                  <p className="text-xs font-medium uppercase text-text-muted">Success Rate</p>
                  <p className="text-2xl font-bold text-success">
                    {performance.success_rate != null ? `${(performance.success_rate * 100).toFixed(0)}%` : 'N/A'}
                  </p>
                </div>
                <div className="space-y-1">
                  <p className="text-xs font-medium uppercase text-text-muted">Avg Duration</p>
                  <p className="text-2xl font-bold text-text">
                    {performance.avg_duration != null ? `${performance.avg_duration}s` : 'N/A'}
                  </p>
                </div>
                <div className="space-y-1">
                  <p className="text-xs font-medium uppercase text-text-muted">Tasks Failed</p>
                  <p className="text-2xl font-bold text-danger">{performance.tasks_failed}</p>
                </div>
              </div>
            ) : (
              <p className="text-sm text-text-muted">No performance data available</p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function TestPanel({
  agent,
  isTestRunning,
  execution,
  onRunTest,
  onCancelTest,
}: {
  agent: AgentDetail | null;
  isTestRunning: boolean;
  execution: TestExecution | null;
  onRunTest: (prompt: string, repositoryId: string | null) => void;
  onCancelTest: () => void;
}) {
  const [prompt, setPrompt] = useState('');
  const [repositoryId, setRepositoryId] = useState<string>('');

  const handleRun = () => {
    if (!prompt.trim()) return;
    onRunTest(prompt.trim(), repositoryId || null);
  };

  return (
    <div className="flex h-full flex-col border-l border-border">
      <div className="border-b border-border p-4">
        <h2 className="mb-3 text-sm font-semibold uppercase text-text-muted">Test Agent</h2>
        {!agent ? (
          <EmptyState
            icon={<Bot className="h-8 w-8" />}
            title="Select an agent"
            description="Choose an agent from the list to run tests"
            className="py-6"
          />
        ) : (
          <div className="space-y-4">
            <div>
              <label className="mb-1.5 block text-sm font-medium text-text">Prompt</label>
              <Textarea
                placeholder="Enter your test prompt..."
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                rows={4}
              />
            </div>
            <div>
              <label className="mb-1.5 block text-sm font-medium text-text">Repository</label>
              <select
                value={repositoryId}
                onChange={(e) => setRepositoryId(e.target.value)}
                className="flex h-10 w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-text focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
              >
                <option value="">Select repository (optional)</option>
                {MOCK_REPOSITORIES.map((repo) => (
                  <option key={repo.id} value={repo.id}>
                    {repo.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex gap-2">
              <Button
                onClick={handleRun}
                disabled={!prompt.trim() || isTestRunning}
                isLoading={isTestRunning}
                leftIcon={isTestRunning ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
              >
                {isTestRunning ? 'Running...' : 'Run Test'}
              </Button>
              {isTestRunning && (
                <Button variant="outline" onClick={onCancelTest} leftIcon={<StopCircle className="h-4 w-4" />}>
                  Cancel
                </Button>
              )}
            </div>
          </div>
        )}
      </div>

      {execution && (
        <div className="flex-1 overflow-y-auto p-4">
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-text">Output</span>
              {execution.status === 'running' && <Loader2 className="h-4 w-4 animate-spin text-info" />}
              {execution.status === 'completed' && <CheckCircle className="h-4 w-4 text-success" />}
              {execution.status === 'error' && <XCircle className="h-4 w-4 text-danger" />}
            </div>
            <div className="rounded-lg border border-border bg-surface p-4">
              <pre className="whitespace-pre-wrap text-sm text-text">
                {execution.output || 'No output yet...'}
              </pre>
            </div>

            {(execution.status === 'completed' || execution.status === 'error') && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">Execution Metrics</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <p className="text-xs text-text-muted">Tokens Used</p>
                      <p className="text-sm font-medium text-text">{execution.tokensUsed.toLocaleString()}</p>
                    </div>
                    <div>
                      <p className="text-xs text-text-muted">Latency</p>
                      <p className="text-sm font-medium text-text">{execution.latencyMs}ms</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function ConfigurationPanel({
  agent,
  onSave,
}: {
  agent: AgentDetail | null;
  onSave: (config: AgentConfig) => void;
}) {
  const [config, setConfig] = useState<AgentConfig>({
    maxIterations: 10,
    timeoutSeconds: 300,
    temperature: 0.7,
    promptTemplate: 'default',
    enabledTools: agent?.tools || [],
  });

  useEffect(() => {
    if (agent) {
      setConfig({
        maxIterations: 10,
        timeoutSeconds: 300,
        temperature: 0.7,
        promptTemplate: 'default',
        enabledTools: agent.tools,
      });
    }
  }, [agent]);

  const toggleTool = (tool: string) => {
    setConfig((prev) => ({
      ...prev,
      enabledTools: prev.enabledTools.includes(tool)
        ? prev.enabledTools.filter((t) => t !== tool)
        : [...prev.enabledTools, tool],
    }));
  };

  if (!agent) return null;

  const allTools = ['read', 'write', 'edit', 'search', 'shell', 'git', 'web', 'memory'];

  return (
    <div className="border-t border-border bg-surface">
      <div className="p-4">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="flex items-center gap-2 text-sm font-semibold uppercase text-text-muted">
            <Settings className="h-4 w-4" />
            Configuration
          </h2>
          <Button
            size="sm"
            onClick={() => onSave(config)}
            leftIcon={<Save className="h-4 w-4" />}
          >
            Save Config
          </Button>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <label className="mb-1 block text-xs font-medium text-text-muted">Max Iterations</label>
            <Input
              type="number"
              min={1}
              max={50}
              value={config.maxIterations}
              onChange={(e) =>
                setConfig((prev) => ({ ...prev, maxIterations: parseInt(e.target.value) || 10 }))
              }
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-text-muted">Timeout (seconds)</label>
            <Input
              type="number"
              min={30}
              max={3600}
              value={config.timeoutSeconds}
              onChange={(e) =>
                setConfig((prev) => ({ ...prev, timeoutSeconds: parseInt(e.target.value) || 300 }))
              }
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-text-muted">Temperature</label>
            <Input
              type="number"
              min={0}
              max={2}
              step={0.1}
              value={config.temperature}
              onChange={(e) =>
                setConfig((prev) => ({ ...prev, temperature: parseFloat(e.target.value) || 0.7 }))
              }
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-text-muted">Prompt Template</label>
            <select
              value={config.promptTemplate}
              onChange={(e) =>
                setConfig((prev) => ({ ...prev, promptTemplate: e.target.value }))
              }
              className="flex h-10 w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-text focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
            >
              {MOCK_PROMPT_TEMPLATES.map((tpl) => (
                <option key={tpl.id} value={tpl.id}>
                  {tpl.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="mt-4">
          <label className="mb-2 block text-xs font-medium text-text-muted">Tool Access</label>
          <div className="flex flex-wrap gap-2">
            {allTools.map((tool) => (
              <button
                key={tool}
                onClick={() => toggleTool(tool)}
                className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium transition-colors ${
                  config.enabledTools.includes(tool)
                    ? 'border-accent bg-accent/10 text-accent'
                    : 'border-border bg-surface text-text-muted hover:bg-surface-hover'
                }`}
              >
                <Wrench className="h-3 w-3" />
                {tool}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export function AgentPlayground() {
  const { agents, selectedAgent, isLoading, fetchAgents, fetchAgent, error, clearError } =
    useStudioStore();

  const [testExecution, setTestExecution] = useState<TestExecution | null>(null);
  const [isTestRunning, setIsTestRunning] = useState(false);

  useEffect(() => {
    fetchAgents();
  }, [fetchAgents]);

  const handleSelectAgent = useCallback(
    (agent: AgentDetail) => {
      fetchAgent(agent.id);
      setTestExecution(null);
      setIsTestRunning(false);
    },
    [fetchAgent]
  );

  const handleRunTest = useCallback(
    async (prompt: string, repositoryId: string | null) => {
      if (!selectedAgent) return;

      setIsTestRunning(true);
      setTestExecution({
        output: '',
        tokensUsed: 0,
        latencyMs: 0,
        status: 'running',
      });

      try {
        const result = await studioService.testAgent(selectedAgent.id, prompt, repositoryId || undefined);
        setTestExecution({
          output: (result as Record<string, unknown>)?.output as string || JSON.stringify(result, null, 2),
          tokensUsed: (result as Record<string, unknown>)?.tokens_used as number || 0,
          latencyMs: (result as Record<string, unknown>)?.latency_ms as number || 0,
          status: 'completed',
        });
      } catch (err) {
        setTestExecution({
          output: err instanceof Error ? err.message : 'Test execution failed',
          tokensUsed: 0,
          latencyMs: 0,
          status: 'error',
        });
      } finally {
        setIsTestRunning(false);
      }
    },
    [selectedAgent]
  );

  const handleCancelTest = useCallback(() => {
    setIsTestRunning(false);
    setTestExecution((prev) =>
      prev ? { ...prev, status: 'error', output: prev.output + '\n\n[Cancelled by user]' } : null
    );
  }, []);

  const handleSaveConfig = useCallback(
    async (config: AgentConfig) => {
      if (!selectedAgent) return;
      try {
        await studioService.updateAgentConfig(selectedAgent.id, {
          max_iterations: config.maxIterations,
          timeout_seconds: config.timeoutSeconds,
          temperature: config.temperature,
          prompt_template: config.promptTemplate,
          tools: config.enabledTools,
        });
      } catch (err) {
        console.error('Failed to save config:', err);
      }
    },
    [selectedAgent]
  );

  return (
    <div className="flex h-full flex-col">
      {error && (
        <div className="flex items-center gap-2 border-b border-danger/20 bg-danger/5 px-4 py-2 text-sm text-danger">
          <AlertTriangle className="h-4 w-4" />
          <span className="flex-1">{error}</span>
          <Button variant="ghost" size="sm" onClick={clearError}>
            Dismiss
          </Button>
        </div>
      )}

      <div className="flex min-h-0 flex-1">
        <div className="w-72 flex-shrink-0">
          <AgentListPanel
            agents={agents}
            selectedAgent={selectedAgent}
            onSelectAgent={handleSelectAgent}
            isLoading={isLoading}
          />
        </div>

        <div className="flex min-w-0 flex-1 flex-col">
          <div className="flex min-h-0 flex-1">
            <div className="flex-1 overflow-hidden">
              {selectedAgent ? (
                <AgentDetailsPanel agent={selectedAgent} />
              ) : (
                <div className="flex h-full items-center justify-center">
                  <EmptyState
                    icon={<Bot className="h-12 w-12" />}
                    title="Select an agent"
                    description="Choose an agent from the sidebar to view details and run tests"
                  />
                </div>
              )}
            </div>

            <div className="w-80 flex-shrink-0">
              <TestPanel
                agent={selectedAgent}
                isTestRunning={isTestRunning}
                execution={testExecution}
                onRunTest={handleRunTest}
                onCancelTest={handleCancelTest}
              />
            </div>
          </div>

          <ConfigurationPanel agent={selectedAgent} onSave={handleSaveConfig} />
        </div>
      </div>
    </div>
  );
}
