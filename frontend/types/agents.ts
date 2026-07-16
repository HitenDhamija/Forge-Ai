export type AgentType = 'planner' | 'executor' | 'reviewer' | 'researcher' | 'orchestrator';

export type AgentStatus = 'idle' | 'running' | 'paused' | 'error' | 'stopped';

export type TaskStatus = 'pending' | 'queued' | 'running' | 'completed' | 'failed' | 'cancelled';

export type TaskPriority = 'low' | 'medium' | 'high' | 'critical';

export type ToolType = 'file' | 'search' | 'git' | 'shell' | 'web' | 'ai' | 'custom';

export interface AgentConfig {
  max_iterations: number;
  timeout_seconds: number;
  temperature: number;
  tools: string[];
  custom_instructions?: string;
}

export interface AgentInfo {
  id: string;
  name: string;
  agent_type: AgentType;
  description: string;
  status: AgentStatus;
  available_tools: string[];
  capabilities?: string[];
  config: AgentConfig;
  created_at: string;
  updated_at: string;
}

export interface TaskStep {
  id: string;
  step_number: number;
  description: string;
  tool_to_use?: string;
  status: TaskStatus;
  result?: string;
  error?: string;
  started_at?: string;
  completed_at?: string;
}

export interface TaskInfo {
  id: string;
  title: string;
  description: string;
  status: TaskStatus;
  priority: TaskPriority;
  agent_id?: string;
  agent_type: AgentType;
  steps: TaskStep[];
  context: Record<string, unknown>;
  result?: string;
  error?: string;
  created_at: string;
  updated_at: string;
  started_at?: string;
  completed_at?: string;
}

export interface TaskRequest {
  title: string;
  description: string;
  task_description?: string;
  agent_type?: AgentType;
  priority?: TaskPriority;
  context?: Record<string, unknown>;
  tools_allowed?: string[];
  max_iterations?: number;
}

export interface AgentMetrics {
  total_agents: number;
  idle_agents: number;
  running_agents: number;
  total_tasks: number;
  completed_tasks: number;
  failed_tasks: number;
  running_tasks: number;
  queued_tasks: number;
}

export interface ToolDefinition {
  name: string;
  description: string;
  tool_type: ToolType;
  parameters: Record<string, unknown>;
  required_permissions: string[];
}
