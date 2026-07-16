import { create } from 'zustand';
import type {
  AgentInfo,
  AgentStatusSummary,
  WorkflowEvent,
} from '@/types/workforce';
import { workforceService } from '@/services/workforce.service';

interface WorkforceState {
  agents: AgentInfo[];
  statusSummary: AgentStatusSummary | null;
  recentEvents: WorkflowEvent[];
  isLoading: boolean;
  error: string | null;

  fetchAgents: () => Promise<void>;
  fetchAgent: (agentId: string) => Promise<AgentInfo | null>;
  fetchStatusSummary: () => Promise<void>;
  fetchRecentEvents: (limit?: number) => Promise<void>;
  processWorkflow: (
    workflowId: string,
    workflowData: Record<string, unknown>
  ) => Promise<Record<string, unknown>>;
  clearError: () => void;
}

export const useWorkforceStore = create<WorkforceState>((set) => ({
  agents: [],
  statusSummary: null,
  recentEvents: [],
  isLoading: false,
  error: null,

  fetchAgents: async () => {
    set({ isLoading: true, error: null });
    try {
      const agents = await workforceService.listAgents();
      set({ agents, isLoading: false });
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : 'Failed to fetch agents',
        isLoading: false,
      });
    }
  },

  fetchAgent: async (agentId) => {
    set({ isLoading: true, error: null });
    try {
      const agent = await workforceService.getAgent(agentId);
      set({ isLoading: false });
      return agent;
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : 'Failed to fetch agent',
        isLoading: false,
      });
      return null;
    }
  },

  fetchStatusSummary: async () => {
    set({ isLoading: true, error: null });
    try {
      const summary = await workforceService.getStatusSummary();
      set({ statusSummary: summary, isLoading: false });
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : 'Failed to fetch status',
        isLoading: false,
      });
    }
  },

  fetchRecentEvents: async (limit) => {
    set({ isLoading: true, error: null });
    try {
      const events = await workforceService.getRecentEvents(limit);
      set({ recentEvents: events, isLoading: false });
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : 'Failed to fetch events',
        isLoading: false,
      });
    }
  },

  processWorkflow: async (workflowId, workflowData) => {
    set({ isLoading: true, error: null });
    try {
      const result = await workforceService.processWorkflow(
        workflowId,
        workflowData
      );
      set({ isLoading: false });
      return result;
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : 'Failed to process workflow',
        isLoading: false,
      });
      throw err;
    }
  },

  clearError: () => set({ error: null }),
}));
