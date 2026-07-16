import { create } from 'zustand';
import type {
  ExecutionSummary,
  WorkflowInfo,
  WorkflowRequest,
} from '@/types/workflows';
import { workflowService } from '@/services/workflow.service';

interface WorkflowState {
  workflows: WorkflowInfo[];
  currentWorkflow: WorkflowInfo | null;
  executionSummary: ExecutionSummary | null;
  isLoading: boolean;
  error: string | null;

  fetchWorkflows: (filters?: { status?: string; project_id?: string }) => Promise<void>;
  fetchWorkflow: (workflowId: string) => Promise<void>;
  createWorkflow: (request: WorkflowRequest) => Promise<WorkflowInfo>;
  approveWorkflow: (workflowId: string) => Promise<void>;
  startWorkflow: (workflowId: string) => Promise<void>;
  pauseWorkflow: (workflowId: string) => Promise<void>;
  resumeWorkflow: (workflowId: string) => Promise<void>;
  cancelWorkflow: (workflowId: string) => Promise<void>;
  fetchExecutionSummary: (workflowId: string) => Promise<void>;
  updateWorkflow: (workflowId: string, data: { title?: string; description?: string; tasks?: { title: string; description: string; priority?: string }[] }) => Promise<void>;
  deleteWorkflow: (workflowId: string) => Promise<void>;
  clearError: () => void;
}

export const useWorkflowStore = create<WorkflowState>((set) => ({
  workflows: [],
  currentWorkflow: null,
  executionSummary: null,
  isLoading: false,
  error: null,

  fetchWorkflows: async (filters) => {
    set({ isLoading: true, error: null });
    try {
      const workflows = await workflowService.listWorkflows(filters);
      set({ workflows, isLoading: false });
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : 'Failed to fetch workflows',
        isLoading: false,
      });
    }
  },

  fetchWorkflow: async (workflowId) => {
    set({ isLoading: true, error: null });
    try {
      const workflow = await workflowService.getWorkflow(workflowId);
      set({ currentWorkflow: workflow, isLoading: false });
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : 'Failed to fetch workflow',
        isLoading: false,
      });
    }
  },

  createWorkflow: async (request) => {
    set({ isLoading: true, error: null });
    try {
      const workflow = await workflowService.createWorkflow(request);
      set((state) => ({
        workflows: [workflow, ...state.workflows],
        currentWorkflow: workflow,
        isLoading: false,
      }));
      return workflow;
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : 'Failed to create workflow',
        isLoading: false,
      });
      throw err;
    }
  },

  approveWorkflow: async (workflowId) => {
    set({ isLoading: true, error: null });
    try {
      const workflow = await workflowService.approveWorkflow(workflowId);
      set((state) => ({
        workflows: state.workflows.map((w) =>
          w.id === workflowId ? workflow : w
        ),
        currentWorkflow:
          state.currentWorkflow?.id === workflowId
            ? workflow
            : state.currentWorkflow,
        isLoading: false,
      }));
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : 'Failed to approve workflow',
        isLoading: false,
      });
    }
  },

  startWorkflow: async (workflowId) => {
    set({ isLoading: true, error: null });
    try {
      const workflow = await workflowService.startWorkflow(workflowId);
      set((state) => ({
        workflows: state.workflows.map((w) =>
          w.id === workflowId ? workflow : w
        ),
        currentWorkflow:
          state.currentWorkflow?.id === workflowId
            ? workflow
            : state.currentWorkflow,
        isLoading: false,
      }));
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : 'Failed to start workflow',
        isLoading: false,
      });
    }
  },

  pauseWorkflow: async (workflowId) => {
    set({ isLoading: true, error: null });
    try {
      const workflow = await workflowService.pauseWorkflow(workflowId);
      set((state) => ({
        workflows: state.workflows.map((w) =>
          w.id === workflowId ? workflow : w
        ),
        currentWorkflow:
          state.currentWorkflow?.id === workflowId
            ? workflow
            : state.currentWorkflow,
        isLoading: false,
      }));
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : 'Failed to pause workflow',
        isLoading: false,
      });
    }
  },

  resumeWorkflow: async (workflowId) => {
    set({ isLoading: true, error: null });
    try {
      const workflow = await workflowService.resumeWorkflow(workflowId);
      set((state) => ({
        workflows: state.workflows.map((w) =>
          w.id === workflowId ? workflow : w
        ),
        currentWorkflow:
          state.currentWorkflow?.id === workflowId
            ? workflow
            : state.currentWorkflow,
        isLoading: false,
      }));
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : 'Failed to resume workflow',
        isLoading: false,
      });
    }
  },

  cancelWorkflow: async (workflowId) => {
    set({ isLoading: true, error: null });
    try {
      const workflow = await workflowService.cancelWorkflow(workflowId);
      set((state) => ({
        workflows: state.workflows.map((w) =>
          w.id === workflowId ? workflow : w
        ),
        currentWorkflow:
          state.currentWorkflow?.id === workflowId
            ? workflow
            : state.currentWorkflow,
        isLoading: false,
      }));
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : 'Failed to cancel workflow',
        isLoading: false,
      });
    }
  },

  fetchExecutionSummary: async (workflowId) => {
    set({ isLoading: true, error: null });
    try {
      const summary = await workflowService.getExecutionSummary(workflowId);
      set({ executionSummary: summary, isLoading: false });
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : 'Failed to fetch summary',
        isLoading: false,
      });
    }
  },

  updateWorkflow: async (workflowId, data) => {
    set({ isLoading: true, error: null });
    try {
      const workflow = await workflowService.updateWorkflow(workflowId, data);
      set((state) => ({
        workflows: state.workflows.map((w) =>
          w.id === workflowId ? workflow : w
        ),
        currentWorkflow:
          state.currentWorkflow?.id === workflowId
            ? workflow
            : state.currentWorkflow,
        isLoading: false,
      }));
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : 'Failed to update workflow',
        isLoading: false,
      });
    }
  },

  deleteWorkflow: async (workflowId) => {
    try {
      await workflowService.deleteWorkflow(workflowId);
      set((state) => ({
        workflows: state.workflows.filter((w) => w.id !== workflowId),
        currentWorkflow:
          state.currentWorkflow?.id === workflowId
            ? null
            : state.currentWorkflow,
      }));
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : 'Failed to delete workflow',
      });
    }
  },

  clearError: () => set({ error: null }),
}));
