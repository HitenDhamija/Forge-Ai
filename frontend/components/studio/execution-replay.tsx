'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { useStudioStore } from '@/stores/studio-store';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Play,
  Pause,
  SkipForward,
  SkipBack,
  Clock,
  Zap,
  Bot,
  Wrench,
  Database,
  GitBranch,
  CheckCircle,
  XCircle,
  AlertTriangle,
  RefreshCw,
  Target,
  Users,
  CircleStop,
  Loader2,
  ChevronRight,
  ChevronLeft,
  FileCode,
} from 'lucide-react';
import type { ReplayState, ReplayEvent } from '@/types/studio';

type EventType = 'agent' | 'tool' | 'memory' | 'decision' | 'execution' | 'system' | 'error';

const EVENT_TYPE_CONFIG: Record<EventType, { label: string; color: string; bgClass: string; textClass: string; icon: React.ReactNode }> = {
  agent: { label: 'Agent', color: 'blue', bgClass: 'bg-blue-500/10', textClass: 'text-blue-500', icon: <Bot className="h-4 w-4" /> },
  tool: { label: 'Tool', color: 'cyan', bgClass: 'bg-cyan-500/10', textClass: 'text-cyan-500', icon: <Wrench className="h-4 w-4" /> },
  memory: { label: 'Memory', color: 'teal', bgClass: 'bg-teal-500/10', textClass: 'text-teal-500', icon: <Database className="h-4 w-4" /> },
  decision: { label: 'Decision', color: 'yellow', bgClass: 'bg-yellow-500/10', textClass: 'text-yellow-500', icon: <GitBranch className="h-4 w-4" /> },
  execution: { label: 'Execution', color: 'red', bgClass: 'bg-red-500/10', textClass: 'text-red-500', icon: <Zap className="h-4 w-4" /> },
  system: { label: 'System', color: 'gray', bgClass: 'bg-gray-500/10', textClass: 'text-gray-500', icon: <Target className="h-4 w-4" /> },
  error: { label: 'Error', color: 'red', bgClass: 'bg-danger/10', textClass: 'text-danger', icon: <XCircle className="h-4 w-4" /> },
};

const SPEED_OPTIONS = [0.5, 1, 2, 4] as const;

const MOCK_EVENTS: ReplayEvent[] = [
  {
    timestamp: '2024-01-15T10:00:00.000Z',
    event_type: 'system',
    node_id: 'start-1',
    agent_id: null,
    tool_id: null,
    data: { message: 'Workflow execution started', workflow_id: 'wf-123' },
    duration_ms: 0,
  },
  {
    timestamp: '2024-01-15T10:00:01.200Z',
    event_type: 'agent',
    node_id: 'planner-1',
    agent_id: 'agent-planner',
    tool_id: null,
    data: { action: 'plan_task', input: 'Analyze the codebase for security vulnerabilities', model: 'gpt-4' },
    duration_ms: 1200,
  },
  {
    timestamp: '2024-01-15T10:00:03.500Z',
    event_type: 'tool',
    node_id: 'tool-1',
    agent_id: 'agent-planner',
    tool_id: 'file_search',
    data: { action: 'search', query: '*.ts', results: ['src/auth.ts', 'src/api.ts', 'src/db.ts'] },
    duration_ms: 2300,
  },
  {
    timestamp: '2024-01-15T10:00:05.800Z',
    event_type: 'memory',
    node_id: 'memory-1',
    agent_id: 'agent-planner',
    tool_id: null,
    data: { action: 'retrieve', query: 'previous security audit results', results: [{ id: 'mem-1', relevance: 0.95, content: 'Last audit found 3 medium issues in auth module' }] },
    duration_ms: 800,
  },
  {
    timestamp: '2024-01-15T10:00:08.100Z',
    event_type: 'decision',
    node_id: 'decision-1',
    agent_id: 'agent-planner',
    tool_id: null,
    data: { question: 'Should we focus on auth module first?', answer: 'Yes', reasoning: 'Previous audit identified issues in auth module' },
    duration_ms: 500,
  },
  {
    timestamp: '2024-01-15T10:00:10.500Z',
    event_type: 'agent',
    node_id: 'agent-1',
    agent_id: 'agent-executor',
    tool_id: null,
    data: { action: 'execute_task', input: 'Run security scanner on auth module', model: 'gpt-4' },
    duration_ms: 2400,
  },
  {
    timestamp: '2024-01-15T10:00:13.000Z',
    event_type: 'tool',
    node_id: 'tool-2',
    agent_id: 'agent-executor',
    tool_id: 'shell',
    data: { command: 'npm audit --json', output: { vulnerabilities: 2, warnings: 5 } },
    duration_ms: 3500,
  },
  {
    timestamp: '2024-01-15T10:00:18.000Z',
    event_type: 'tool',
    node_id: 'tool-3',
    agent_id: 'agent-executor',
    tool_id: 'code_review',
    data: { file: 'src/auth.ts', issues: [{ line: 42, severity: 'medium', message: 'Potential XSS vulnerability' }] },
    duration_ms: 2000,
  },
  {
    timestamp: '2024-01-15T10:00:21.500Z',
    event_type: 'execution',
    node_id: 'execution-1',
    agent_id: null,
    tool_id: null,
    data: { action: 'run_tests', test_suite: 'security', passed: 15, failed: 2 },
    duration_ms: 4500,
  },
  {
    timestamp: '2024-01-15T10:00:27.000Z',
    event_type: 'error',
    node_id: 'agent-1',
    agent_id: 'agent-executor',
    tool_id: null,
    data: { error: 'Test failed: auth.test.ts', stack: 'AssertionError: Expected true to be false' },
    duration_ms: 100,
  },
  {
    timestamp: '2024-01-15T10:00:28.500Z',
    event_type: 'agent',
    node_id: 'reflection-1',
    agent_id: 'agent-reviewer',
    tool_id: null,
    data: { action: 'review_results', findings: ['2 vulnerabilities found', '5 warnings', '2 test failures'], recommendation: 'Fix critical issues before deployment' },
    duration_ms: 1500,
  },
  {
    timestamp: '2024-01-15T10:00:31.000Z',
    event_type: 'system',
    node_id: 'end-1',
    agent_id: null,
    tool_id: null,
    data: { message: 'Workflow execution completed', status: 'completed', total_duration_ms: 31000 },
    duration_ms: 0,
  },
];

function getEventType(eventType: string): EventType {
  if (eventType in EVENT_TYPE_CONFIG) return eventType as EventType;
  return 'system';
}

function formatDuration(ms: number): string {
  if (ms === 0) return '0ms';
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

function formatTimestamp(isoString: string): string {
  const date = new Date(isoString);
  return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

function ReplayControls({
  state,
  isPlaying,
  speed,
  onPlayPause,
  onStepForward,
  onStepBackward,
  onSpeedChange,
}: {
  state: ReplayState | null;
  isPlaying: boolean;
  speed: number;
  onPlayPause: () => void;
  onStepForward: () => void;
  onStepBackward: () => void;
  onSpeedChange: (speed: number) => void;
}) {
  const currentIndex = state?.current_index ?? 0;
  const totalEvents = state?.total_events ?? 0;
  const progress = totalEvents > 0 ? (currentIndex / totalEvents) * 100 : 0;

  return (
    <div className="flex items-center gap-4 border-b border-border bg-surface px-4 py-3">
      <div className="flex items-center gap-2">
        <Button
          variant="ghost"
          size="icon"
          onClick={onStepBackward}
          disabled={currentIndex <= 0}
          title="Step Backward"
        >
          <SkipBack className="h-4 w-4" />
        </Button>

        <Button
          variant={isPlaying ? 'secondary' : 'default'}
          size="icon"
          onClick={onPlayPause}
          title={isPlaying ? 'Pause' : 'Play'}
        >
          {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
        </Button>

        <Button
          variant="ghost"
          size="icon"
          onClick={onStepForward}
          disabled={currentIndex >= totalEvents - 1}
          title="Step Forward"
        >
          <SkipForward className="h-4 w-4" />
        </Button>
      </div>

      <div className="flex items-center gap-2">
        {SPEED_OPTIONS.map((s) => (
          <button
            key={s}
            onClick={() => onSpeedChange(s)}
            className={`rounded px-2 py-1 text-xs font-medium transition-colors ${
              speed === s
                ? 'bg-accent/20 text-accent'
                : 'bg-surface-hover text-text-muted hover:text-text'
            }`}
          >
            {s}x
          </button>
        ))}
      </div>

      <div className="flex-1">
        <div className="h-2 overflow-hidden rounded-full bg-surface-hover">
          <div
            className="h-full rounded-full bg-accent transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      <div className="flex items-center gap-2 text-sm text-text-muted">
        <Clock className="h-4 w-4" />
        <span className="font-medium tabular-nums">
          {currentIndex + 1} / {totalEvents}
        </span>
      </div>
    </div>
  );
}

function TimelineView({
  events,
  currentIndex,
  onSelectEvent,
}: {
  events: ReplayEvent[];
  currentIndex: number;
  onSelectEvent: (index: number) => void;
}) {
  const listRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const activeElement = listRef.current?.querySelector('[data-active="true"]');
    if (activeElement) {
      activeElement.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  }, [currentIndex]);

  if (events.length === 0) {
    return (
      <div className="flex h-full items-center justify-center text-text-muted">
        <p>No events to display</p>
      </div>
    );
  }

  return (
    <div ref={listRef} className="overflow-y-auto p-4">
      <div className="relative">
        <div className="absolute left-[19px] top-0 bottom-0 w-0.5 bg-border" />

        <div className="space-y-1">
          {events.map((event, index) => {
            const eventType = getEventType(event.event_type);
            const config = EVENT_TYPE_CONFIG[eventType];
            const isActive = index === currentIndex;
            const isPast = index < currentIndex;

            return (
              <button
                key={index}
                data-active={isActive}
                onClick={() => onSelectEvent(index)}
                className={`relative flex w-full items-start gap-3 rounded-lg p-2 text-left transition-colors ${
                  isActive
                    ? 'bg-accent/10 border border-accent/30'
                    : isPast
                      ? 'border border-transparent opacity-60 hover:opacity-100'
                      : 'border border-transparent hover:bg-surface-hover'
                }`}
              >
                <div className="relative z-10 mt-1 flex h-5 w-5 flex-shrink-0 items-center justify-center">
                  <div
                    className={`h-3 w-3 rounded-full border-2 ${
                      isActive
                        ? 'border-accent bg-accent'
                        : isPast
                          ? 'border-text-muted bg-text-muted'
                          : 'border-border bg-surface'
                    }`}
                  />
                </div>

                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <div className={`rounded p-0.5 ${config.bgClass}`}>
                      <span className={config.textClass}>{config.icon}</span>
                    </div>
                    <span className={`text-sm font-medium ${isActive ? 'text-text' : 'text-text-secondary'}`}>
                      {config.label}
                    </span>
                    {event.agent_id && (
                      <Badge variant="outline" className="text-xs">
                        {event.agent_id}
                      </Badge>
                    )}
                    {event.tool_id && (
                      <Badge variant="secondary" className="text-xs">
                        {event.tool_id}
                      </Badge>
                    )}
                  </div>

                  <div className="mt-1 flex items-center gap-3 text-xs text-text-muted">
                    <span>{formatTimestamp(event.timestamp)}</span>
                    {event.duration_ms > 0 && (
                      <span className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {formatDuration(event.duration_ms)}
                      </span>
                    )}
                    <span className="text-text-secondary truncate">
                      {event.node_id}
                    </span>
                  </div>
                </div>

                {isActive && <ChevronRight className="mt-1 h-4 w-4 flex-shrink-0 text-accent" />}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function EventDetailPanel({ event, index }: { event: ReplayEvent | null; index: number }) {
  if (!event) {
    return (
      <div className="flex h-full items-center justify-center p-6 text-text-muted">
        <div className="text-center">
          <FileCode className="mx-auto mb-2 h-8 w-8 opacity-50" />
          <p className="text-sm">Select an event to view details</p>
        </div>
      </div>
    );
  }

  const eventType = getEventType(event.event_type);
  const config = EVENT_TYPE_CONFIG[eventType];

  return (
    <div className="flex h-full flex-col overflow-hidden border-l border-border">
      <div className="border-b border-border p-4">
        <div className="mb-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className={`rounded p-1 ${config.bgClass}`}>
              <span className={config.textClass}>{config.icon}</span>
            </div>
            <h3 className="text-sm font-semibold text-text">{config.label} Event</h3>
          </div>
          <Badge variant={eventType === 'error' ? 'destructive' : 'default'}>
            Event #{index + 1}
          </Badge>
        </div>

        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-text-muted">Timestamp</span>
            <span className="font-mono text-text">{formatTimestamp(event.timestamp)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-text-muted">Duration</span>
            <span className="font-mono text-text">{formatDuration(event.duration_ms)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-text-muted">Node</span>
            <span className="font-mono text-text">{event.node_id}</span>
          </div>
          {event.agent_id && (
            <div className="flex justify-between">
              <span className="text-text-muted">Agent</span>
              <span className="font-mono text-text">{event.agent_id}</span>
            </div>
          )}
          {event.tool_id && (
            <div className="flex justify-between">
              <span className="text-text-muted">Tool</span>
              <span className="font-mono text-text">{event.tool_id}</span>
            </div>
          )}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Event Data</CardTitle>
            </CardHeader>
            <CardContent>
              <pre className="overflow-x-auto whitespace-pre-wrap rounded-md bg-surface-hover p-3 text-xs text-text">
                {JSON.stringify(event.data, null, 2)}
              </pre>
            </CardContent>
          </Card>

          {eventType === 'tool' && 'action' in event.data && (
            <Card>
              <CardHeader>
                <CardTitle className="text-sm">Tool Call Details</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-text-muted">Action</span>
                    <span className="text-text">{String(event.data.action)}</span>
                  </div>
                  {'command' in event.data && (
                    <div>
                      <span className="text-xs text-text-muted">Command</span>
                      <pre className="mt-1 overflow-x-auto whitespace-pre-wrap rounded bg-surface-hover p-2 text-xs text-text">
                        {String(event.data.command)}
                      </pre>
                    </div>
                  )}
                  {'query' in event.data && (
                    <div className="flex justify-between text-sm">
                      <span className="text-text-muted">Query</span>
                      <span className="text-text">{String(event.data.query)}</span>
                    </div>
                  )}
                  {'output' in event.data && (
                    <div>
                      <span className="text-xs text-text-muted">Output</span>
                      <pre className="mt-1 overflow-x-auto whitespace-pre-wrap rounded bg-surface-hover p-2 text-xs text-text">
                        {typeof event.data.output === 'string'
                          ? event.data.output
                          : JSON.stringify(event.data.output, null, 2)}
                      </pre>
                    </div>
                  )}
                  {'results' in event.data && Array.isArray(event.data.results) && (
                    <div>
                      <span className="text-xs text-text-muted">Results ({(event.data.results as unknown[]).length} items)</span>
                      <pre className="mt-1 overflow-x-auto whitespace-pre-wrap rounded bg-surface-hover p-2 text-xs text-text">
                        {JSON.stringify(event.data.results, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          {eventType === 'agent' && (
            <Card>
              <CardHeader>
                <CardTitle className="text-sm">Agent Decision</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {'action' in event.data && (
                    <div className="flex justify-between text-sm">
                      <span className="text-text-muted">Action</span>
                      <span className="text-text">{String(event.data.action)}</span>
                    </div>
                  )}
                  {'input' in event.data && (
                    <div>
                      <span className="text-xs text-text-muted">Input</span>
                      <pre className="mt-1 overflow-x-auto whitespace-pre-wrap rounded bg-surface-hover p-2 text-xs text-text">
                        {String(event.data.input)}
                      </pre>
                    </div>
                  )}
                  {'model' in event.data && (
                    <div className="flex justify-between text-sm">
                      <span className="text-text-muted">Model</span>
                      <Badge variant="outline">{String(event.data.model)}</Badge>
                    </div>
                  )}
                  {'recommendation' in event.data && (
                    <div>
                      <span className="text-xs text-text-muted">Recommendation</span>
                      <p className="mt-1 text-sm text-text">{String(event.data.recommendation)}</p>
                    </div>
                  )}
                  {'findings' in event.data && Array.isArray(event.data.findings) && (
                    <div>
                      <span className="text-xs text-text-muted">Findings</span>
                      <ul className="mt-1 list-inside list-disc text-sm text-text">
                        {(event.data.findings as string[]).map((finding, i) => (
                          <li key={i}>{finding}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          {eventType === 'memory' && (
            <Card>
              <CardHeader>
                <CardTitle className="text-sm">Memory Retrieval</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {'query' in event.data && (
                    <div className="flex justify-between text-sm">
                      <span className="text-text-muted">Query</span>
                      <span className="text-text">{String(event.data.query)}</span>
                    </div>
                  )}
                  {'results' in event.data && Array.isArray(event.data.results) && (
                    <div className="space-y-2">
                      <span className="text-xs text-text-muted">
                        Results ({(event.data.results as unknown[]).length} items)
                      </span>
                      {(event.data.results as Record<string, unknown>[]).map((result, i) => (
                        <div
                          key={i}
                          className="rounded border border-border bg-surface-hover p-2"
                        >
                          {'relevance' in result && (
                            <div className="mb-1 flex items-center gap-2 text-xs">
                              <span className="text-text-muted">Relevance:</span>
                              <div className="h-1.5 w-16 overflow-hidden rounded-full bg-surface">
                                <div
                                  className="h-full bg-accent"
                                  style={{ width: `${Number(result.relevance) * 100}%` }}
                                />
                              </div>
                              <span className="text-text">
                                {(Number(result.relevance) * 100).toFixed(0)}%
                              </span>
                            </div>
                          )}
                          {'content' in result && (
                            <p className="text-xs text-text">{String(result.content)}</p>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          {eventType === 'error' && (
            <Card className="border-danger/30">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-sm text-danger">
                  <AlertTriangle className="h-4 w-4" />
                  Error Details
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {'error' in event.data && (
                    <div>
                      <span className="text-xs text-text-muted">Error</span>
                      <pre className="mt-1 overflow-x-auto whitespace-pre-wrap rounded bg-danger/10 p-2 text-xs text-danger">
                        {String(event.data.error)}
                      </pre>
                    </div>
                  )}
                  {'stack' in event.data && (
                    <div>
                      <span className="text-xs text-text-muted">Stack Trace</span>
                      <pre className="mt-1 overflow-x-auto whitespace-pre-wrap rounded bg-surface-hover p-2 text-xs text-text">
                        {String(event.data.stack)}
                      </pre>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}

function ExecutionSummary({ events }: { events: ReplayEvent[] }) {
  const totalDuration = events.reduce((sum, e) => sum + e.duration_ms, 0);
  const eventCounts = events.reduce(
    (acc, e) => {
      const type = getEventType(e.event_type);
      acc[type] = (acc[type] || 0) + 1;
      return acc;
    },
    {} as Record<EventType, number>
  );

  const errorCount = eventCounts.error || 0;
  const hasErrors = errorCount > 0;

  return (
    <div className="border-t border-border bg-surface px-4 py-3">
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-2">
          <Clock className="h-4 w-4 text-text-muted" />
          <span className="text-sm text-text-muted">Duration:</span>
          <span className="text-sm font-medium text-text">{formatDuration(totalDuration)}</span>
        </div>

        <div className="h-4 w-px bg-border" />

        <div className="flex flex-wrap items-center gap-3">
          {Object.entries(eventCounts).map(([type, count]) => {
            const config = EVENT_TYPE_CONFIG[type as EventType];
            return (
              <div key={type} className="flex items-center gap-1.5">
                <div className={`rounded p-0.5 ${config.bgClass}`}>
                  <span className={config.textClass}>{config.icon}</span>
                </div>
                <span className="text-xs text-text-muted">{config.label}:</span>
                <span className="text-xs font-medium text-text">{count}</span>
              </div>
            );
          })}
        </div>

        <div className="h-4 w-px bg-border" />

        <div className="flex items-center gap-2">
          {hasErrors ? (
            <>
              <XCircle className="h-4 w-4 text-danger" />
              <span className="text-sm font-medium text-danger">
                {errorCount} error{errorCount !== 1 ? 's' : ''}
              </span>
            </>
          ) : (
            <>
              <CheckCircle className="h-4 w-4 text-success" />
              <span className="text-sm font-medium text-success">Completed successfully</span>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export function ExecutionReplay({ executionId }: { executionId?: string }) {
  const { replayState, replayEvents, fetchReplay, fetchReplayEvents, stepReplayForward } =
    useStudioStore();

  const [events, setEvents] = useState<ReplayEvent[]>(MOCK_EVENTS);
  const [state, setState] = useState<ReplayState | null>({
    execution_id: executionId || 'mock-execution',
    workflow_id: 'wf-123',
    current_index: 0,
    status: 'paused',
    total_events: MOCK_EVENTS.length,
    speed: 1,
  });

  const [isPlaying, setIsPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);
  const [selectedEventIndex, setSelectedEventIndex] = useState<number | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (executionId) {
      fetchReplay(executionId);
      fetchReplayEvents(executionId);
    }
  }, [executionId, fetchReplay, fetchReplayEvents]);

  useEffect(() => {
    if (replayState) setState(replayState);
    if (replayEvents.length > 0) setEvents(replayEvents);
  }, [replayState, replayEvents]);

  const handleStepForward = useCallback(() => {
    if (!state) return;
    if (state.current_index < events.length - 1) {
      const newIndex = state.current_index + 1;
      setState((prev) => (prev ? { ...prev, current_index: newIndex } : null));
      setSelectedEventIndex(newIndex);
    }
  }, [state, events.length]);

  const handleStepBackward = useCallback(() => {
    if (!state) return;
    if (state.current_index > 0) {
      const newIndex = state.current_index - 1;
      setState((prev) => (prev ? { ...prev, current_index: newIndex } : null));
      setSelectedEventIndex(newIndex);
    }
  }, [state]);

  const handlePlayPause = useCallback(() => {
    setIsPlaying((prev) => !prev);
  }, []);

  const handleSpeedChange = useCallback((newSpeed: number) => {
    setSpeed(newSpeed);
  }, []);

  const handleSelectEvent = useCallback((index: number) => {
    setSelectedEventIndex(index);
    setState((prev) => (prev ? { ...prev, current_index: index } : null));
  }, []);

  useEffect(() => {
    if (isPlaying) {
      intervalRef.current = setInterval(
        () => {
          handleStepForward();
        },
        1000 / speed
      );
    } else if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [isPlaying, speed, handleStepForward]);

  useEffect(() => {
    if (state && state.current_index >= events.length - 1 && isPlaying) {
      setIsPlaying(false);
    }
  }, [state, events.length, isPlaying]);

  const currentEvent = state ? events[state.current_index] ?? null : null;

  return (
    <div className="flex h-full flex-col">
      <ReplayControls
        state={state}
        isPlaying={isPlaying}
        speed={speed}
        onPlayPause={handlePlayPause}
        onStepForward={handleStepForward}
        onStepBackward={handleStepBackward}
        onSpeedChange={handleSpeedChange}
      />

      <div className="flex min-h-0 flex-1">
        <div className="w-1/2 overflow-hidden border-r border-border">
          <div className="border-b border-border px-4 py-2">
            <h2 className="text-xs font-semibold uppercase text-text-muted">Timeline</h2>
          </div>
          <TimelineView
            events={events}
            currentIndex={state?.current_index ?? 0}
            onSelectEvent={handleSelectEvent}
          />
        </div>

        <div className="w-1/2">
          <div className="border-b border-border px-4 py-2">
            <h2 className="text-xs font-semibold uppercase text-text-muted">Event Detail</h2>
          </div>
          <EventDetailPanel
            event={selectedEventIndex !== null ? events[selectedEventIndex] : currentEvent}
            index={selectedEventIndex ?? (state?.current_index ?? 0)}
          />
        </div>
      </div>

      <ExecutionSummary events={events} />
    </div>
  );
}
