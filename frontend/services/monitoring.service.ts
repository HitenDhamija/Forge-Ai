import { apiClient } from './api';
import type {
  OverviewData,
  AgentSnapshot,
  WorkflowSnapshot,
  ToolSnapshot,
  MemoryStatus,
  PromptStatus,
  ExecutionSnapshot,
  HealthSummary,
  TimelineEvent,
  AnalyticsData,
} from '@/types/monitoring';

const MONITORING_ENDPOINTS = {
  OVERVIEW: '/monitoring/overview',
  WORKFLOWS: '/monitoring/workflows',
  AGENTS: '/monitoring/agents',
  TOOLS: '/monitoring/tools',
  MEMORY: '/monitoring/memory',
  PROMPTS: '/monitoring/prompts',
  ANALYTICS: '/monitoring/analytics',
  HEALTH: '/monitoring/health',
  TIMELINE: '/monitoring/timeline',
  EXECUTIONS: '/monitoring/executions',
};

function unwrap<T>(response: any): T {
  return response.data?.data ?? response.data;
}

function unwrapList<T>(response: any): T[] {
  const data = response.data?.data ?? response.data;
  return Array.isArray(data) ? data : [];
}

function parseStatusBreakdown(input: any): Record<string, number> {
  if (!input) return {};
  // Handle dict format from backend (e.g. {"idle": 3, "running": 1})
  if (typeof input === 'object' && !Array.isArray(input)) {
    const result: Record<string, number> = {};
    for (const [key, val] of Object.entries(input)) {
      result[key] = typeof val === 'number' ? val : parseInt(String(val), 10) || 0;
    }
    return result;
  }
  // Handle string format (e.g. "idle=3,running=1")
  if (typeof input !== 'string') return {};
  const result: Record<string, number> = {};
  input.split(',').filter(Boolean).forEach((part) => {
    const [key, val] = part.split('=');
    if (key && val) result[key.trim()] = parseInt(val.trim(), 10) || 0;
  });
  return result;
}

function transformOverview(raw: any): OverviewData {
  const a = raw?.agents || {};
  const w = raw?.workflows || {};
  const t = raw?.tools || {};
  const m = raw?.memory || {};
  const e = raw?.execution || {};
  const h = raw?.health || {};

  const agentBreakdown = parseStatusBreakdown(a.status_breakdown);
  const workflowBreakdown = parseStatusBreakdown(w.status_breakdown);

  // Health components come as an array of objects directly
  const healthComponents: any[] = Array.isArray(h.components) ? h.components : [];

  // Parse workflow performance
  const perf = typeof w.performance === 'string' ? {} : (w.performance || {});

  return {
    agents: {
      total: a.total_agents || 0,
      idle: agentBreakdown.idle || agentBreakdown.unknown || 0,
      running: agentBreakdown.running || agentBreakdown.executing || 0,
      error: agentBreakdown.error || 0,
      health_breakdown: parseStatusBreakdown(a.health_breakdown || ''),
    },
    workflows: {
      total: w.total_workflows || 0,
      running: workflowBreakdown.running || 0,
      completed: workflowBreakdown.completed || 0,
      failed: workflowBreakdown.failed || 0,
      success_rate: perf.success_rate || 0,
    },
    tools: {
      total: t.total_unique_tools || 0,
      healthy: parseStatusBreakdown(t.health_breakdown || '').healthy || 0,
      offline: parseStatusBreakdown(t.health_breakdown || '').offline || 0,
      avg_latency: t.avg_latency || t.avg_latency_ms || 0,
    },
    memory: {
      total_chunks: m.total_operations || 0,
      total_repositories: 0,
    },
    execution: {
      total: e.performance?.total_executions || 0,
      running: e.active_count || 0,
      completed: e.performance?.completed || 0,
      failed: e.performance?.failed || 0,
    },
    health: {
      overall: h.overall_status || 'unknown',
      components: healthComponents,
      checked_at: h.timestamp || new Date().toISOString(),
    },
  };
}

export const monitoringService = {
  async getOverview(): Promise<OverviewData> {
    const response = await apiClient.get<any>(MONITORING_ENDPOINTS.OVERVIEW);
    const raw = unwrap<any>(response);
    return transformOverview(raw);
  },

  async getWorkflows(): Promise<WorkflowSnapshot[]> {
    const response = await apiClient.get<any>(MONITORING_ENDPOINTS.WORKFLOWS);
    return unwrapList<WorkflowSnapshot>(response);
  },

  async getAgents(): Promise<AgentSnapshot[]> {
    const response = await apiClient.get<any>(MONITORING_ENDPOINTS.AGENTS);
    return unwrapList<AgentSnapshot>(response);
  },

  async getTools(): Promise<ToolSnapshot[]> {
    const response = await apiClient.get<any>(MONITORING_ENDPOINTS.TOOLS);
    return unwrapList<ToolSnapshot>(response);
  },

  async getMemory(): Promise<MemoryStatus> {
    const response = await apiClient.get<any>(MONITORING_ENDPOINTS.MEMORY);
    const raw = unwrap<any>(response);
    return {
      total_chunks: raw?.total_chunks || raw?.total_operations || 0,
      total_repositories: raw?.total_repositories || 0,
      collections: raw?.collections || 0,
      embedding_model: raw?.embedding_model || 'unknown',
      avg_search_time: raw?.avg_search_time || 0,
      total_searches: raw?.total_searches || 0,
      cache_hit_rate: raw?.cache_hit_rate || 0,
    };
  },

  async getPrompts(): Promise<PromptStatus> {
    const response = await apiClient.get<any>(MONITORING_ENDPOINTS.PROMPTS);
    const raw = unwrap<any>(response);
    return {
      total_prompts: raw?.total_prompts || 0,
      avg_latency: raw?.avg_latency || 0,
      avg_tokens: raw?.avg_tokens || 0,
      avg_confidence: raw?.avg_confidence || 0,
      success_rate: raw?.success_rate || 0,
      models_used: raw?.models_used || [],
      top_templates: raw?.top_templates || [],
    };
  },

  async getAnalytics(timeRange?: string): Promise<AnalyticsData> {
    const response = await apiClient.get<any>(MONITORING_ENDPOINTS.ANALYTICS, {
      params: timeRange ? { time_range: timeRange } : undefined,
    });
    const raw = unwrap<any>(response);
    return {
      daily_activity: raw?.daily_activity || [],
      execution_trend: raw?.execution_trend || { metric: 'executions', current: 0, previous: 0, change_percent: 0, direction: 'stable' as const },
      success_trend: raw?.success_trend || { metric: 'success_rate', current: 0, previous: 0, change_percent: 0, direction: 'stable' as const },
      most_active_agent: raw?.most_active_agent || {},
      most_used_tool: raw?.most_used_tool || {},
    };
  },

  async getHealth(): Promise<HealthSummary> {
    const response = await apiClient.get<any>(MONITORING_ENDPOINTS.HEALTH);
    const raw = unwrap<any>(response);
    const components = Array.isArray(raw?.components) ? raw.components : [];
    return {
      overall: raw?.overall_status || raw?.overall || 'unknown',
      components: components.map((c: any) => ({
        name: c.name || 'Unknown',
        status: c.status || 'unknown',
        latency_ms: c.latency_ms || 0,
        message: c.message || '',
        last_checked: c.last_checked || new Date().toISOString(),
        version: c.version || null,
      })),
      checked_at: raw?.timestamp || raw?.checked_at || new Date().toISOString(),
    };
  },

  async getTimeline(params?: {
    hours?: number;
    event_type?: string;
    source?: string;
    limit?: number;
  }): Promise<TimelineEvent[]> {
    const response = await apiClient.get<any>(MONITORING_ENDPOINTS.TIMELINE, { params });
    return unwrapList<TimelineEvent>(response);
  },

  async getExecutions(): Promise<ExecutionSnapshot[]> {
    const response = await apiClient.get<any>(MONITORING_ENDPOINTS.EXECUTIONS);
    return unwrapList<ExecutionSnapshot>(response);
  },
};
