export type AgentRole =
  | 'supervisor'
  | 'software_engineer'
  | 'qa_engineer'
  | 'code_reviewer'
  | 'technical_writer'
  | 'devops_engineer'
  | 'database_engineer'
  | 'research_engineer';

export type AgentStatus =
  | 'idle'
  | 'assigned'
  | 'preparing'
  | 'waiting'
  | 'executing'
  | 'reviewing'
  | 'completed'
  | 'failed'
  | 'unavailable'
  | 'offline';

export interface Capability {
  name: string;
  description: string;
  level: number;
  tools: string[];
  task_types: string[];
}

export interface Policy {
  allowed_tasks: string[];
  forbidden_tasks: string[];
  allowed_tools: string[];
  forbidden_tools: string[];
  repository_access: string[];
  max_concurrent_tasks: number;
  max_retries: number;
  timeout_seconds: number;
}

export interface AgentMemory {
  short_term: Record<string, unknown>[];
  task_memory: Record<string, unknown>[];
  execution_context: Record<string, unknown>;
  conversation_state: Record<string, unknown>[];
}

export interface AgentInfo {
  id: string;
  role: AgentRole;
  name: string;
  description: string;
  status: AgentStatus;
  capabilities: Capability[];
  policies: Policy;
  memory: AgentMemory;
  version: string;
  created_at: string;
  updated_at: string;
  last_heartbeat: string | null;
}

export interface AgentStatusSummary {
  total_agents: number;
  idle_agents: number;
  busy_agents: number;
  unavailable_agents: number;
  agents_by_role: Record<string, number>;
}

export interface WorkflowEvent {
  id: string;
  type: string;
  data: Record<string, unknown>;
  timestamp: string;
}

export interface TaskAssignment {
  task_id: string;
  workflow_id: string;
  agent_id: string;
  title: string;
  description: string;
  context: Record<string, unknown>;
  required_capabilities: string[];
  priority: string;
  timeout_seconds: number;
}
