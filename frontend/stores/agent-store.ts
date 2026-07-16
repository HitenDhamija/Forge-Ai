import { create } from 'zustand';
import type {
  AgentInfo,
  AgentMetrics,
  TaskInfo,
  TaskRequest,
} from '@/types/agents';
import { agentService } from '@/services/agent.service';

interface AgentState {
  agents: AgentInfo[];
  tasks: TaskInfo[];
  currentTask: TaskInfo | null;
  metrics: AgentMetrics | null;
  isLoading: boolean;
  error: string | null;

  fetchAgents: () => Promise<void>;
  fetchTasks: (filters?: { status?: string; agent_type?: string }) => Promise<void>;
  fetchTask: (taskId: string) => Promise<void>;
  createTask: (request: TaskRequest) => Promise<TaskInfo>;
  cancelTask: (taskId: string) => Promise<void>;
  fetchMetrics: () => Promise<void>;
  clearError: () => void;
}

export const useAgentStore = create<AgentState>((set) => ({
  agents: [],
  tasks: [],
  currentTask: null,
  metrics: null,
  isLoading: false,
  error: null,

  fetchAgents: async () => {
    set({ isLoading: true, error: null });
    try {
      const agents = await agentService.listAgents();
      set({ agents, isLoading: false });
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : 'Failed to fetch agents',
        isLoading: false,
      });
    }
  },

  fetchTasks: async (filters) => {
    set({ isLoading: true, error: null });
    try {
      const tasks = await agentService.listTasks(filters);
      set({ tasks, isLoading: false });
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : 'Failed to fetch tasks',
        isLoading: false,
      });
    }
  },

  fetchTask: async (taskId) => {
    set({ isLoading: true, error: null });
    try {
      const task = await agentService.getTask(taskId);
      set({ currentTask: task, isLoading: false });
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : 'Failed to fetch task',
        isLoading: false,
      });
    }
  },

  createTask: async (request) => {
    set({ isLoading: true, error: null });
    try {
      const task = await agentService.createTask(request);
      set((state) => ({
        tasks: [task, ...state.tasks],
        currentTask: task,
        isLoading: false,
      }));
      return task;
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : 'Failed to create task',
        isLoading: false,
      });
      throw err;
    }
  },

  cancelTask: async (taskId) => {
    set({ isLoading: true, error: null });
    try {
      const updatedTask = await agentService.cancelTask(taskId);
      set((state) => ({
        tasks: state.tasks.map((t) =>
          t.id === taskId ? updatedTask : t
        ),
        currentTask:
          state.currentTask?.id === taskId
            ? updatedTask
            : state.currentTask,
        isLoading: false,
      }));
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : 'Failed to cancel task',
        isLoading: false,
      });
    }
  },

  fetchMetrics: async () => {
    set({ isLoading: true, error: null });
    try {
      const metrics = await agentService.getMetrics();
      set({ metrics, isLoading: false });
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : 'Failed to fetch metrics',
        isLoading: false,
      });
    }
  },

  clearError: () => set({ error: null }),
}));
