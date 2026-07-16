export type NodeType =
  | 'start'
  | 'planner'
  | 'supervisor'
  | 'agent'
  | 'decision'
  | 'approval'
  | 'reflection'
  | 'tool'
  | 'memory'
  | 'execution'
  | 'end';

export type NodeStatus = 'idle' | 'running' | 'completed' | 'failed' | 'waiting';

export interface NodePosition {
  x: number;
  y: number;
}

export interface WorkflowNode {
  id: string;
  type: NodeType;
  label: string;
  position: NodePosition;
  data: Record<string, unknown>;
  status: NodeStatus;
}

export interface WorkflowEdge {
  id: string;
  source: string;
  target: string;
  label: string;
}

export interface WorkflowGraph {
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
}

export interface NodeTemplate {
  type: NodeType;
  label: string;
  description: string;
  icon: string;
  color: string;
  defaultData: Record<string, unknown>;
}

export interface PromptVersion {
  version: number;
  created_by: string;
  created_at: string;
  comment: string;
}

export interface PromptTemplate {
  id: string;
  name: string;
  description: string;
  content: string;
  variables: string[];
  current_version: number;
  tags: string[];
  versions: PromptVersion[];
  versions_count: number;
}

export interface PromptTestResult {
  output: string;
  tokens_used: number;
  latency_ms: number;
  confidence: number;
}

export interface ReplayEvent {
  timestamp: string;
  event_type: string;
  node_id: string;
  agent_id: string | null;
  tool_id: string | null;
  data: Record<string, unknown>;
  duration_ms: number;
}

export interface ReplayState {
  execution_id: string;
  workflow_id: string;
  current_index: number;
  status: string;
  total_events: number;
  speed: number;
}

export interface AgentPerformance {
  tasks_completed: number;
  tasks_failed: number;
  avg_duration: number;
  success_rate: number;
  last_active: string | null;
}

export interface AgentDetail {
  id: string;
  role: string;
  name: string;
  description: string;
  status: string;
  capabilities: string[];
  tools: string[];
  performance: AgentPerformance | null;
}

export interface WorkspaceItem {
  id: string;
  type: string;
  name: string;
  description: string;
  updated_at: string;
}

export interface WorkspaceOverview {
  total_items: number;
  by_type: Record<string, number>;
  recent_items: WorkspaceItem[];
  bookmarks: WorkspaceItem[];
}
