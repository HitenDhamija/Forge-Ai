export interface Organization {
  id: string;
  name: string;
  description: string;
  owner_id: string;
  settings: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  repositories?: OrganizationRepository[];
  stats?: OrganizationStats;
}

export interface OrganizationRepository {
  id: string;
  organization_id: string;
  repository_id: string | null;
  repository_name: string;
  repository_path: string;
  project_id: string | null;
  status: string;
  added_at: string;
}

export interface OrganizationStats {
  repositories: number;
  knowledge: number;
  templates: number;
  collaborations: number;
  comparisons?: number;
}

export interface SharedKnowledge {
  id: string;
  organization_id: string;
  knowledge_type: string;
  title: string;
  description: string;
  content: Record<string, unknown>;
  source_repository_id: string | null;
  tags: string[];
  confidence: number;
  usage_count: number;
  created_at: string;
}

export interface WorkflowTemplate {
  id: string;
  organization_id: string;
  name: string;
  description: string;
  template_type: string;
  template_data: Record<string, unknown>;
  tags: string[];
  usage_count: number;
  is_default: boolean;
  created_at: string;
}

export interface Collaboration {
  id: string;
  organization_id: string;
  collaboration_type: string;
  entity_type: string;
  entity_id: string;
  user_id: string;
  content: string;
  created_at: string;
}

export interface ComparisonResult {
  id: string;
  organization_id: string;
  repository_a_id: string;
  repository_b_id: string;
  comparison_type: string;
  result: {
    similarities: Array<{ type: string; description: string }>;
    differences: Array<{ type: string; description: string }>;
    score: number;
  };
  created_at: string;
}

export interface GraphNode {
  id: string;
  type: string;
  label: string;
  x: number;
  y: number;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  relationship: string;
}

export interface OrganizationGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface SearchResult {
  id: string;
  type: string;
  title: string;
  description: string;
  score: number;
}

export interface Recommendation {
  id: string;
  type: string;
  title: string;
  description: string;
  source_repository: string;
  confidence: number;
}
