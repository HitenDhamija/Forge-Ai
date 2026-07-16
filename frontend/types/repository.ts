export type ImportMethod = "zip" | "git" | "folder";
export type RepositoryStatus = "importing" | "analyzing" | "ready" | "error";
export type ArchitectureStyle =
  | "mvc"
  | "clean"
  | "layered"
  | "microservices"
  | "monolith"
  | "serverless"
  | "unknown";

export interface RepositoryCreate {
  name: string;
  description?: string;
  import_method: ImportMethod;
  source_url?: string;
  source_path?: string;
}

export interface RepositoryInfo {
  id: string;
  name: string;
  description: string | null;
  status: RepositoryStatus;
  import_method: ImportMethod;
  source_url: string | null;
  local_path: string;
  created_at: string;
  analyzed_at: string | null;
  error_message: string | null;
}

export interface LanguageInfo {
  name: string;
  file_count: number;
  total_lines: number;
  percentage: number;
  extensions: string[];
}

export interface FrameworkInfo {
  name: string;
  version: string | null;
  confidence: number;
  evidence: string[];
}

export interface DependencyInfo {
  name: string;
  version: string | null;
  is_production: boolean;
  source_file: string;
}

export interface FolderInfo {
  name: string;
  path: string;
  purpose: string;
  file_count: number;
  children: FolderInfo[];
}

export interface ArchitectureSummary {
  style: ArchitectureStyle;
  description: string;
  entry_points: string[];
  main_modules: string[];
  authentication_detected: boolean;
  database_detected: boolean;
  api_detected: boolean;
  frontend_detected: boolean;
}

export interface CodeElement {
  name: string;
  type: string;
  file_path: string;
  line_start: number;
  line_end: number | null;
  docstring: string | null;
  decorators: string[];
  parent_class: string | null;
  parameters: string[];
  return_type: string | null;
  imports: string[];
  is_exported: boolean;
}

export interface RouteInfo {
  method: string;
  path: string;
  function_name: string;
  file_path: string;
  line_number: number;
  middleware: string[];
  authentication_required: boolean;
  parameters: string[];
  response_model: string | null;
}

export interface DatabaseModelInfo {
  name: string;
  table_name: string | null;
  file_path: string;
  line_number: number;
  fields: CodeElement[];
  relationships: string[];
  primary_key: string | null;
  foreign_keys: string[];
}

export interface AnalysisResult {
  repository_id: string;
  analyzed_at: string;
  languages: LanguageInfo[];
  frameworks: FrameworkInfo[];
  dependencies: DependencyInfo[];
  folder_structure: FolderInfo[];
  architecture: ArchitectureSummary;
  code_elements: CodeElement[];
  routes: RouteInfo[];
  database_models: DatabaseModelInfo[];
  import_graph: any[];
  config_files: string[];
  entry_points: string[];
  total_files: number;
  total_lines: number;
  analysis_time_ms: number;
}

export interface GraphNode {
  id: string;
  type: string;
  name: string;
  metadata: Record<string, any>;
}

export interface GraphEdge {
  source: string;
  target: string;
  relationship: string;
}

export interface SemanticGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
  root_id: string;
}
