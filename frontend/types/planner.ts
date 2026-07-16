export type IntentType =
  | "coding"
  | "debugging"
  | "documentation"
  | "architecture"
  | "testing"
  | "database"
  | "deployment"
  | "research"
  | "refactoring"
  | "code_review"
  | "planning"
  | "learning"
  | "unknown";

export type ComplexityLevel =
  | "simple"
  | "medium"
  | "complex"
  | "very_complex";

export type TaskPriority = "low" | "medium" | "high" | "critical";

export type TaskStatus =
  | "pending"
  | "in_progress"
  | "completed"
  | "blocked"
  | "skipped";

export type RiskLevel = "low" | "medium" | "high" | "critical";

export interface Task {
  id: string;
  title: string;
  description: string;
  dependencies: string[];
  estimated_time_minutes: number | null;
  complexity: ComplexityLevel;
  required_skills: string[];
  required_context: string[];
  priority: TaskPriority;
  status: TaskStatus;
  files_affected: string[];
  notes: string | null;
}

export interface Risk {
  level: RiskLevel;
  category: string;
  description: string;
  mitigation: string | null;
  affected_tasks: string[];
}

export interface DependencyInfo {
  type: string;
  name: string;
  path: string | null;
  required_by: string[];
  exists: boolean;
}

export interface ArchitectureNote {
  category: string;
  content: string;
  related_tasks: string[];
}

export interface ExecutionPlan {
  id: string;
  objective: string;
  intent: IntentType;
  complexity: ComplexityLevel;
  tasks: Task[];
  risks: Risk[];
  dependencies: DependencyInfo[];
  architecture_notes: ArchitectureNote[];
  files_affected: string[];
  estimated_duration_minutes: number;
  approval_required: boolean;
  created_at: string;
  repository_id: string | null;
  repository_name: string | null;
  context_summary: string | null;
}

export interface PlanRequest {
  objective: string;
  repository_id?: string;
  repository_name?: string;
  additional_context?: string;
  constraints?: string[];
}

export interface PlanHistoryItem {
  id: string;
  objective: string;
  intent: IntentType;
  complexity: ComplexityLevel;
  task_count: number;
  risk_count: number;
  estimated_duration_minutes: number;
  created_at: string;
  repository_name: string | null;
}
