export type WorkflowStatus =
  | 'created'
  | 'draft'
  | 'waiting_approval'
  | 'ready'
  | 'running'
  | 'paused'
  | 'failed'
  | 'cancelled'
  | 'completed';

export type TaskStatus =
  | 'pending'
  | 'ready'
  | 'running'
  | 'waiting'
  | 'failed'
  | 'skipped'
  | 'completed'
  | 'retrying';

export type TaskPriority = 'low' | 'medium' | 'high' | 'critical';

export type RiskLevel = 'low' | 'medium' | 'high' | 'critical';

export type EventType =
  | 'workflow_created'
  | 'workflow_started'
  | 'workflow_paused'
  | 'workflow_resumed'
  | 'workflow_cancelled'
  | 'workflow_completed'
  | 'workflow_failed'
  | 'task_created'
  | 'task_started'
  | 'task_completed'
  | 'task_failed'
  | 'task_retrying'
  | 'task_skipped'
  | 'approval_requested'
  | 'approval_granted'
  | 'approval_denied';

export interface TaskRequest {
  title: string;
  description: string;
  priority?: TaskPriority;
  dependencies?: string[];
  agent_type?: string;
  estimated_duration?: number;
  metadata?: Record<string, unknown>;
}

export interface WorkflowRequest {
  title: string;
  description: string;
  project_id?: string;
  tasks: TaskRequest[];
  requires_approval?: boolean;
  risk_level?: RiskLevel;
  metadata?: Record<string, unknown>;
}

export interface TaskInfo {
  id: string;
  workflow_id: string;
  title: string;
  description: string;
  priority: TaskPriority;
  dependencies: string[];
  agent_type: string | null;
  status: TaskStatus;
  retries: number;
  max_retries: number;
  execution_result: Record<string, unknown> | null;
  validation_result: Record<string, unknown> | null;
  duration: number | null;
  created_at: string;
  updated_at: string;
  started_at: string | null;
  completed_at: string | null;
}

export interface WorkflowInfo {
  id: string;
  project_id: string | null;
  title: string;
  description: string;
  summary?: string;
  status: WorkflowStatus;
  current_step: number;
  tasks: TaskInfo[];
  execution_log: Record<string, unknown>[];
  approval_status: string | null;
  risk_level: RiskLevel;
  estimated_time: number | null;
  created_at: string;
  updated_at: string;
  started_at: string | null;
  completed_at: string | null;
  metadata: Record<string, unknown>;
}

export interface WorkflowEvent {
  id: string;
  workflow_id: string;
  task_id: string | null;
  event_type: EventType;
  data: Record<string, unknown>;
  timestamp: string;
}

export interface ExecutionSummary {
  workflow_id: string;
  total_tasks: number;
  completed_tasks: number;
  failed_tasks: number;
  skipped_tasks: number;
  total_duration: number;
  events: WorkflowEvent[];
  success_rate: number;
  average_task_duration: number;
}

export interface ValidationResult {
  is_valid: boolean;
  errors: string[];
  warnings: string[];
  dependency_cycles: string[][];
  ready_tasks: string[];
}
