export type ComponentHealth = 'healthy' | 'degraded' | 'unhealthy' | 'unknown';

export type AgentHealthStatus = 'healthy' | 'degraded' | 'unhealthy' | 'offline';

export type EventSeverity = 'info' | 'warning' | 'error';

export type TimelineEventType =
  | 'workflow_started'
  | 'workflow_completed'
  | 'workflow_failed'
  | 'task_started'
  | 'task_completed'
  | 'task_failed'
  | 'agent_assigned'
  | 'tool_called'
  | 'tool_completed'
  | 'reflection_started'
  | 'qa_started'
  | 'approval_requested'
  | 'approval_granted'
  | 'memory_indexed'
  | 'memory_searched'
  | 'learning_processed'
  | 'execution_started'
  | 'execution_completed'
  | 'system_health_check';

export interface AgentSnapshot {
  agent_id: string;
  name: string;
  agent_type: string;
  status: string;
  current_task_id: string | null;
  tasks_completed: number;
  tasks_failed: number;
  avg_execution_time: number;
  last_active: string | null;
}

export interface WorkflowSnapshot {
  workflow_id: string;
  title: string;
  status: string;
  progress: number;
  tasks_total: number;
  tasks_completed: number;
  tasks_failed: number;
  elapsed_time: number;
  risk_level: string;
}

export interface ToolSnapshot {
  tool_id: string;
  name: string;
  provider: string;
  status: string;
  total_calls: number;
  success_count: number;
  error_count: number;
  avg_latency: number;
  health_status: string;
}

export interface MemoryStatus {
  total_chunks: number;
  total_repositories: number;
  collections: number;
  embedding_model: string;
  avg_search_time: number;
  total_searches: number;
  cache_hit_rate: number;
}

export interface PromptStatus {
  total_prompts: number;
  avg_latency: number;
  avg_tokens: number;
  avg_confidence: number;
  success_rate: number;
  models_used: string[];
  top_templates: string[];
}

export interface ExecutionSnapshot {
  execution_id: string;
  workflow_id: string;
  status: string;
  progress: number;
  steps_total: number;
  steps_completed: number;
  steps_failed: number;
  elapsed_time: number;
  current_step: number | null;
  current_agent: string | null;
}

export interface ComponentStatus {
  name: string;
  status: ComponentHealth;
  latency_ms: number;
  message: string;
  last_checked: string;
  version: string | null;
}

export interface HealthSummary {
  overall: ComponentHealth;
  components: ComponentStatus[];
  checked_at: string;
}

export interface TimelineEvent {
  id: string;
  event_type: TimelineEventType;
  source: string;
  title: string;
  description: string;
  severity: EventSeverity;
  timestamp: string;
}

export interface DailyActivity {
  period: string;
  workflows_started: number;
  workflows_completed: number;
  tasks_completed: number;
  tools_used: number;
}

export interface TrendData {
  metric: string;
  current: number;
  previous: number;
  change_percent: number;
  direction: 'up' | 'down' | 'stable';
}

export interface AnalyticsData {
  daily_activity: DailyActivity[];
  execution_trend: TrendData;
  success_trend: TrendData;
  most_active_agent: Record<string, unknown>;
  most_used_tool: Record<string, unknown>;
}

export interface OverviewData {
  agents: {
    total: number;
    idle: number;
    running: number;
    error: number;
    health_breakdown: Record<string, number>;
  };
  workflows: {
    total: number;
    running: number;
    completed: number;
    failed: number;
    success_rate: number;
  };
  tools: {
    total: number;
    healthy: number;
    offline: number;
    avg_latency: number;
  };
  memory: {
    total_chunks: number;
    total_repositories: number;
  };
  execution: {
    total: number;
    running: number;
    completed: number;
    failed: number;
  };
  health: HealthSummary;
}
