export type DevOpsStatus = 'pending' | 'analyzing' | 'generating' | 'validating' | 'scoring' | 'reporting' | 'completed' | 'failed';

export type ArtifactType = 'dockerfile' | 'compose' | 'compose_dev' | 'github_actions' | 'kubernetes' | 'report' | 'all';

export type SecuritySeverity = 'critical' | 'high' | 'medium' | 'low' | 'info';

export type SecurityCategory = 'secrets' | 'environment' | 'docker' | 'dependencies' | 'network' | 'configuration' | 'image';

export interface SecurityIssue {
  category: SecurityCategory;
  severity: SecuritySeverity;
  title: string;
  description: string;
  file_path: string;
  line_number: number | null;
  recommendation: string;
}

export interface SecurityValidation {
  issues: SecurityIssue[];
  score: number;
  categories_checked: string[];
  total_issues: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
}

export interface ScoreItem {
  dimension: string;
  score: number;
  weight: number;
  details: string[];
  recommendations: string[];
}

export interface ProductionScore {
  overall_score: number;
  dimensions: ScoreItem[];
  grade: string;
  recommendations: string[];
  timestamp: string;
}

export interface InfrastructureComponent {
  type: string;
  name: string;
  version: string;
  port: number | null;
  config: Record<string, unknown>;
}

export interface DeploymentAnalysis {
  project_type: string;
  components: InfrastructureComponent[];
  env_vars: string[];
  ports: number[];
  volumes: string[];
  services: string[];
  strategy: string;
  docker_present: boolean;
  compose_present: boolean;
  ci_cd_present: boolean;
}

export interface DockerfileResult {
  content: string;
  stages: string[];
  base_image: string;
  size_estimate: string;
  security_notes: string[];
}

export interface ComposeResult {
  content: string;
  variant: string;
  services_count: number;
  volumes_count: number;
  networks_count: number;
  notes: string[];
}

export interface WorkflowInfo {
  filename: string;
  content: string;
  type: string;
}

export interface GitHubActionsResult {
  workflows: WorkflowInfo[];
  total_workflows: number;
}

export interface K8sResource {
  resource_type: string;
  name: string;
  namespace: string;
  content: string;
  labels: Record<string, string>;
}

export interface KubernetesResult {
  resources: K8sResource[];
  namespace: string;
  total_resources: number;
}

export interface DeploymentReport {
  project_name: string;
  timestamp: string;
  sections: ReportSection[];
  plan: DeploymentPlan;
  diagram: InfrastructureDiagram;
  score: number;
  format: string;
}

export interface ReportSection {
  title: string;
  content: string;
  severity: string;
  order: number;
}

export interface DeploymentPlan {
  strategy: string;
  containers: ContainerSpec[];
  ports: Record<string, number>;
  volumes: VolumeSpec[];
  secrets: string[];
  scaling: ScalingConfig;
  rollback: RollbackConfig;
  monitoring: MonitoringConfig;
}

export interface ContainerSpec {
  name: string;
  image: string;
  ports: number[];
  env_count: number;
}

export interface VolumeSpec {
  name: string;
  mount_path: string;
  type: string;
}

export interface ScalingConfig {
  min_replicas: number;
  max_replicas: number;
  target_cpu: number;
  target_memory: number;
}

export interface RollbackConfig {
  strategy: string;
  max_history: number;
  auto_rollback: boolean;
}

export interface MonitoringConfig {
  health_check_path: string;
  metrics_port: number;
  logging_level: string;
}

export interface InfrastructureDiagram {
  services: DiagramService[];
  connections: DiagramConnection[];
  description: string;
}

export interface DiagramService {
  name: string;
  type: string;
  port: number | null;
}

export interface DiagramConnection {
  from: string;
  to: string;
  protocol: string;
}

export interface DevOpsTask {
  task_id: string;
  status: DevOpsStatus;
  artifacts: Record<string, unknown>;
  analysis: DeploymentAnalysis | null;
  security: SecurityValidation | null;
  score: ProductionScore | null;
}

export interface ArtifactResponse {
  task_id: string;
  status: string;
  artifacts: Record<string, unknown>;
  analysis: DeploymentAnalysis | null;
  security: SecurityValidation | null;
  score: ProductionScore | null;
}

export interface ReportResponse {
  task_id: string;
  report: DeploymentReport;
  score: ProductionScore | null;
}

export interface TaskListItem {
  task_id: string;
  repository_id: string;
  status: DevOpsStatus;
  description: string;
  has_score: boolean;
  overall_score: number | null;
  started_at: string;
  completed_at: string | null;
}
