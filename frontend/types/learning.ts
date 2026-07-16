export type ExperienceType =
  | 'architecture'
  | 'bug_fix'
  | 'deployment'
  | 'database'
  | 'testing'
  | 'performance'
  | 'security'
  | 'documentation'
  | 'refactoring';

export type OutcomeType = 'success' | 'failure' | 'partial';

export type PatternType =
  | 'architecture'
  | 'coding'
  | 'security'
  | 'deployment'
  | 'testing'
  | 'database'
  | 'frontend'
  | 'backend';

export type LessonType =
  | 'failure'
  | 'rejection'
  | 'regression'
  | 'violation'
  | 'security_issue'
  | 'performance_issue';

export type FeedbackType = 'helpful' | 'incorrect' | 'needs_improvement' | 'excellent';

export type Severity = 'critical' | 'high' | 'medium' | 'low';

export type Priority = 'high' | 'medium' | 'low';

export interface Experience {
  id: string;
  workflow_id: string | null;
  repository_id: string | null;
  experience_type: ExperienceType;
  title: string;
  description: string;
  context: Record<string, unknown>;
  outcome: OutcomeType;
  solution: string;
  files_changed: string[];
  technologies: string[];
  tags: string[];
  confidence: number;
  reuse_potential: number;
  complexity: number;
  success_rate: number;
  generalization_score: number;
  feedback_score: number | null;
  created_at: string;
  updated_at: string;
}

export interface Pattern {
  id: string;
  experience_id: string | null;
  pattern_type: PatternType;
  name: string;
  description: string;
  code_example: string | null;
  when_to_use: string;
  when_not_to_use: string;
  technologies: string[];
  tags: string[];
  confidence: number;
  usage_count: number;
  success_count: number;
  success_rate: number;
  generalization_score: number;
  created_at: string;
  updated_at: string;
}

export interface Lesson {
  id: string;
  experience_id: string | null;
  lesson_type: LessonType;
  title: string;
  description: string;
  root_cause: string;
  avoidance_strategy: string;
  severity: Severity;
  technologies: string[];
  tags: string[];
  confidence: number;
  times_encountered: number;
  created_at: string;
  updated_at: string;
}

export interface Recommendation {
  id: string;
  pattern_id: string | null;
  task_type: string;
  context_keywords: string[];
  recommendation: string;
  title?: string;
  description?: string;
  recommendation_type?: string;
  source_name?: string;
  source_experience_id?: string;
  source_pattern_id?: string;
  source_lesson_id?: string;
  confidence: number;
  priority: Priority;
  technologies: string[];
  tags?: string[];
  rationale?: string;
  created_at: string;
  updated_at: string;
}

export interface Feedback {
  id: string;
  experience_id: string | null;
  feedback_type: FeedbackType;
  rating: number | null;
  comment: string | null;
  context: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface LearningStats {
  total_tasks: number;
  total_experiences: number;
  total_patterns: number;
  total_lessons: number;
  total_recommendations: number;
  successful_experiences: number;
  failed_experiences: number;
  success_rate: number;
}

export interface GrowthAnalytics {
  timeline: GrowthTimelineEntry[];
  total_tasks: number;
}

export interface GrowthTimelineEntry {
  date: string;
  experiences: number;
  patterns: number;
  lessons: number;
}

export interface LearningTask {
  task_id: string;
  workflow_id: string | null;
  repository_id: string | null;
  status: string;
  experiences_count: number;
  patterns_count: number;
  lessons_count: number;
  started_at: string;
  completed_at: string | null;
}

export interface ProcessWorkflowRequest {
  workflow_id: string;
  repository_id?: string;
  title?: string;
  description?: string;
  outcome?: string;
  files_changed?: string[];
  technologies?: string[];
  context?: Record<string, unknown>;
  execution_data?: Record<string, unknown>;
  reflection_data?: Record<string, unknown>;
  qa_data?: Record<string, unknown>;
  review_data?: Record<string, unknown>;
}

export interface ProcessResponse {
  task_id: string;
  status: string;
  experiences_count: number;
  patterns_count: number;
  lessons_count: number;
  recommendations_count: number;
  experiences: Experience[];
  patterns: Pattern[];
  lessons: Lesson[];
  recommendations: Recommendation[];
}

export interface RecommendationRequest {
  task_type: string;
  context_keywords?: string[];
  technologies?: string[];
  description?: string;
}

export interface FeedbackRequest {
  experience_id: string;
  feedback_type: FeedbackType;
  rating?: number;
  comment?: string;
}
