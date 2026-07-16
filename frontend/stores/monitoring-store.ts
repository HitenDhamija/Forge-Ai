import { create } from 'zustand';
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
import { monitoringService } from '@/services/monitoring.service';

interface MonitoringState {
  overview: OverviewData | null;
  agents: AgentSnapshot[];
  workflows: WorkflowSnapshot[];
  tools: ToolSnapshot[];
  memory: MemoryStatus | null;
  prompts: PromptStatus | null;
  executions: ExecutionSnapshot[];
  health: HealthSummary | null;
  timeline: TimelineEvent[];
  analytics: AnalyticsData | null;
  isLoading: boolean;
  error: string | null;
  lastRefresh: string | null;

  fetchOverview: () => Promise<void>;
  fetchAgents: () => Promise<void>;
  fetchWorkflows: () => Promise<void>;
  fetchTools: () => Promise<void>;
  fetchMemory: () => Promise<void>;
  fetchPrompts: () => Promise<void>;
  fetchExecutions: () => Promise<void>;
  fetchHealth: () => Promise<void>;
  fetchTimeline: (params?: {
    hours?: number;
    event_type?: string;
    source?: string;
  }) => Promise<void>;
  fetchAnalytics: (timeRange?: string) => Promise<void>;
  refreshAll: () => Promise<void>;
  clearError: () => void;
}

export const useMonitoringStore = create<MonitoringState>((set) => ({
  overview: null,
  agents: [],
  workflows: [],
  tools: [],
  memory: null,
  prompts: null,
  executions: [],
  health: null,
  timeline: [],
  analytics: null,
  isLoading: false,
  error: null,
  lastRefresh: null,

  fetchOverview: async () => {
    set({ isLoading: true, error: null });
    try {
      const overview = await monitoringService.getOverview();
      set({ overview, isLoading: false, lastRefresh: new Date().toISOString() });
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : 'Failed to fetch overview',
        isLoading: false,
      });
    }
  },

  fetchAgents: async () => {
    set({ isLoading: true, error: null });
    try {
      const agents = await monitoringService.getAgents();
      set({ agents, isLoading: false });
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : 'Failed to fetch agents',
        isLoading: false,
      });
    }
  },

  fetchWorkflows: async () => {
    set({ isLoading: true, error: null });
    try {
      const workflows = await monitoringService.getWorkflows();
      set({ workflows, isLoading: false });
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : 'Failed to fetch workflows',
        isLoading: false,
      });
    }
  },

  fetchTools: async () => {
    set({ isLoading: true, error: null });
    try {
      const tools = await monitoringService.getTools();
      set({ tools, isLoading: false });
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : 'Failed to fetch tools',
        isLoading: false,
      });
    }
  },

  fetchMemory: async () => {
    set({ isLoading: true, error: null });
    try {
      const memory = await monitoringService.getMemory();
      set({ memory, isLoading: false });
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : 'Failed to fetch memory',
        isLoading: false,
      });
    }
  },

  fetchPrompts: async () => {
    set({ isLoading: true, error: null });
    try {
      const prompts = await monitoringService.getPrompts();
      set({ prompts, isLoading: false });
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : 'Failed to fetch prompts',
        isLoading: false,
      });
    }
  },

  fetchExecutions: async () => {
    set({ isLoading: true, error: null });
    try {
      const executions = await monitoringService.getExecutions();
      set({ executions, isLoading: false });
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : 'Failed to fetch executions',
        isLoading: false,
      });
    }
  },

  fetchHealth: async () => {
    set({ isLoading: true, error: null });
    try {
      const health = await monitoringService.getHealth();
      set({ health, isLoading: false });
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : 'Failed to fetch health',
        isLoading: false,
      });
    }
  },

  fetchTimeline: async (params) => {
    set({ isLoading: true, error: null });
    try {
      const timeline = await monitoringService.getTimeline(params);
      set({ timeline, isLoading: false });
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : 'Failed to fetch timeline',
        isLoading: false,
      });
    }
  },

  fetchAnalytics: async (timeRange) => {
    set({ isLoading: true, error: null });
    try {
      const analytics = await monitoringService.getAnalytics(timeRange);
      set({ analytics, isLoading: false });
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : 'Failed to fetch analytics',
        isLoading: false,
      });
    }
  },

  refreshAll: async () => {
    set({ isLoading: true, error: null });
    try {
      const results = await Promise.allSettled([
        monitoringService.getOverview(),
        monitoringService.getAgents(),
        monitoringService.getWorkflows(),
        monitoringService.getTools(),
        monitoringService.getMemory(),
        monitoringService.getExecutions(),
        monitoringService.getHealth(),
      ]);

      const get = <T>(r: PromiseSettledResult<T>, fallback: T): T =>
        r.status === 'fulfilled' ? r.value : fallback;

      set({
        overview: get(results[0], null as any),
        agents: get(results[1], []),
        workflows: get(results[2], []),
        tools: get(results[3], []),
        memory: get(results[4], null as any),
        executions: get(results[5], []),
        health: get(results[6], null as any),
        isLoading: false,
        lastRefresh: new Date().toISOString(),
      });
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : 'Failed to refresh',
        isLoading: false,
      });
    }
  },

  clearError: () => set({ error: null }),
}));
