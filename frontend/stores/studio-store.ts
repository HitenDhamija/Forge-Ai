import { create } from 'zustand';
import type {
  WorkflowGraph,
  NodeTemplate,
  PromptTemplate,
  ReplayState,
  ReplayEvent,
  AgentDetail,
  WorkspaceOverview,
} from '@/types/studio';
import { studioService } from '@/services/studio.service';

type StudioSection = 'workflows' | 'prompts' | 'replay' | 'agents' | 'workspace' | 'models' | 'memory';

interface StudioState {
  activeSection: StudioSection;
  setActiveSection: (section: StudioSection) => void;

  // Workflow Builder
  workflowGraph: WorkflowGraph | null;
  nodeTemplates: NodeTemplate[];
  selectedNodeId: string | null;

  // Saved Workflows
  savedWorkflows: Array<{
    id: string;
    name: string;
    description: string;
    project_id: string | null;
    nodes: unknown[];
    edges: unknown[];
    created_at: string;
    updated_at: string;
  }>;
  currentWorkflowId: string | null;
  currentWorkflowName: string;
  currentWorkflowDescription: string;
  currentProjectId: string | null;

  // Prompt Studio
  prompts: PromptTemplate[];
  selectedPrompt: PromptTemplate | null;

  // Replay
  replayState: ReplayState | null;
  replayEvents: ReplayEvent[];

  // Agent Playground
  agents: AgentDetail[];
  selectedAgent: AgentDetail | null;

  // Workspace
  workspace: WorkspaceOverview | null;

  // UI State
  isLoading: boolean;
  error: string | null;
  sidebarCollapsed: boolean;
  toggleSidebar: () => void;

  // Execution State
  isExecuting: boolean;
  executionResults: Array<{
    node_id: string;
    status: string;
    output: Record<string, unknown>;
    duration_ms: number;
    error?: string;
  }> | null;
  executionStatus: 'idle' | 'running' | 'completed' | 'failed';
  executingNodeId: string | null;

  // Actions
  fetchWorkflowGraph: (workflowId: string) => Promise<void>;
  fetchNodeTemplates: () => Promise<void>;
  setSelectedNode: (nodeId: string | null) => void;

  fetchPrompts: () => Promise<void>;
  fetchPrompt: (promptId: string) => Promise<void>;

  fetchReplay: (executionId: string) => Promise<void>;
  fetchReplayEvents: (executionId: string) => Promise<void>;
  stepReplayForward: (executionId: string) => Promise<void>;

  fetchAgents: () => Promise<void>;
  fetchAgent: (agentId: string) => Promise<void>;

  fetchWorkspace: () => Promise<void>;

  clearError: () => void;
  executeWorkflow: (nodes: unknown[], edges: unknown[], inputs?: Record<string, unknown>) => Promise<void>;
  clearExecution: () => void;
  setExecutingNodeId: (nodeId: string | null) => void;

  // Workflow Persistence
  loadSavedWorkflows: (projectId?: string) => Promise<void>;
  saveCurrentWorkflow: () => Promise<void>;
  loadWorkflow: (workflowId: string) => void;
  deleteWorkflow: (workflowId: string) => Promise<void>;
  setCurrentWorkflowName: (name: string) => void;
  setCurrentWorkflowDescription: (desc: string) => void;
  setCurrentProjectId: (projectId: string | null) => void;
  newWorkflow: () => void;
}

export const useStudioStore = create<StudioState>((set) => ({
  activeSection: 'workflows',
  setActiveSection: (section) => set({ activeSection: section }),

  workflowGraph: null,
  nodeTemplates: [],
  selectedNodeId: null,

  savedWorkflows: [],
  currentWorkflowId: null,
  currentWorkflowName: 'Untitled Workflow',
  currentWorkflowDescription: '',
  currentProjectId: null,

  prompts: [],
  selectedPrompt: null,

  replayState: null,
  replayEvents: [],

  agents: [],
  selectedAgent: null,

  workspace: null,

  isLoading: false,
  error: null,
  sidebarCollapsed: false,
  isExecuting: false,
  executionResults: null,
  executionStatus: 'idle',
  executingNodeId: null,
  toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),

  fetchWorkflowGraph: async (workflowId) => {
    set({ isLoading: true, error: null });
    try {
      const graph = await studioService.getWorkflowGraph(workflowId);
      set({ workflowGraph: graph, isLoading: false });
    } catch (err) {
      set({ error: err instanceof Error ? err.message : 'Failed to fetch workflow graph', isLoading: false });
    }
  },

  fetchNodeTemplates: async () => {
    try {
      const templates = await studioService.getNodeTemplates();
      set({ nodeTemplates: templates });
    } catch (err) {
      set({ error: err instanceof Error ? err.message : 'Failed to fetch node templates' });
    }
  },

  setSelectedNode: (nodeId) => set({ selectedNodeId: nodeId }),

  fetchPrompts: async () => {
    set({ isLoading: true, error: null });
    try {
      const prompts = await studioService.listPrompts();
      set({ prompts, isLoading: false });
    } catch (err) {
      set({ error: err instanceof Error ? err.message : 'Failed to fetch prompts', isLoading: false });
    }
  },

  fetchPrompt: async (promptId) => {
    set({ isLoading: true, error: null });
    try {
      const prompt = await studioService.getPrompt(promptId);
      set({ selectedPrompt: prompt, isLoading: false });
    } catch (err) {
      set({ error: err instanceof Error ? err.message : 'Failed to fetch prompt', isLoading: false });
    }
  },

  fetchReplay: async (executionId) => {
    set({ isLoading: true, error: null });
    try {
      const state = await studioService.getReplay(executionId);
      set({ replayState: state, isLoading: false });
    } catch (err) {
      set({ error: err instanceof Error ? err.message : 'Failed to fetch replay', isLoading: false });
    }
  },

  fetchReplayEvents: async (executionId) => {
    try {
      const events = await studioService.getReplayEvents(executionId);
      set({ replayEvents: events });
    } catch (err) {
      set({ error: err instanceof Error ? err.message : 'Failed to fetch replay events' });
    }
  },

  stepReplayForward: async (executionId) => {
    try {
      const event = await studioService.stepForward(executionId);
      if (event) {
        set((state) => ({
          replayEvents: [...state.replayEvents, event],
          replayState: state.replayState
            ? { ...state.replayState, current_index: state.replayState.current_index + 1 }
            : null,
        }));
      }
    } catch (err) {
      set({ error: err instanceof Error ? err.message : 'Failed to step forward' });
    }
  },

  fetchAgents: async () => {
    set({ isLoading: true, error: null });
    try {
      const agents = await studioService.listAgents();
      set({ agents, isLoading: false });
    } catch (err) {
      set({ error: err instanceof Error ? err.message : 'Failed to fetch agents', isLoading: false });
    }
  },

  fetchAgent: async (agentId) => {
    set({ isLoading: true, error: null });
    try {
      const agent = await studioService.getAgent(agentId);
      set({ selectedAgent: agent, isLoading: false });
    } catch (err) {
      set({ error: err instanceof Error ? err.message : 'Failed to fetch agent', isLoading: false });
    }
  },

  fetchWorkspace: async () => {
    set({ isLoading: true, error: null });
    try {
      const workspace = await studioService.getWorkspace();
      set({ workspace, isLoading: false });
    } catch (err) {
      set({ error: err instanceof Error ? err.message : 'Failed to fetch workspace', isLoading: false });
    }
  },

  clearError: () => set({ error: null }),

  executeWorkflow: async (nodes, edges, inputs) => {
    set({ isExecuting: true, executionStatus: 'running', executionResults: null, error: null });

    try {
      const results: Array<{
        node_id: string;
        node_type: string;
        label: string;
        status: string;
        output: Record<string, unknown>;
        duration_ms: number;
        error?: string;
        llm_model?: string;
        tokens_used?: number;
      }> = [];

      for await (const event of studioService.executeWorkflowStream(nodes, edges, inputs)) {
        if (event.type === 'node_start' && event.node_id) {
          set({ executingNodeId: event.node_id });
        } else if (event.type === 'node_complete' && event.node_id) {
          results.push({
            node_id: event.node_id,
            node_type: event.node_type || '',
            label: event.label || '',
            status: 'completed',
            output: event.output || {},
            duration_ms: event.duration_ms || 0,
            llm_model: event.llm_model,
            tokens_used: event.tokens_used,
          });
          set({ executionResults: [...results], executingNodeId: null });
        } else if (event.type === 'node_error' && event.node_id) {
          results.push({
            node_id: event.node_id,
            node_type: event.node_type || '',
            label: event.label || '',
            status: 'failed',
            output: event.output || {},
            duration_ms: event.duration_ms || 0,
            error: event.error,
          });
          set({ executionResults: [...results], executingNodeId: null });
        } else if (event.type === 'workflow_complete') {
          set({
            isExecuting: false,
            executionStatus: event.status === 'completed' ? 'completed' : 'failed',
            executionResults: results,
            executingNodeId: null,
          });
        }
      }
    } catch (err) {
      set({
        isExecuting: false,
        executionStatus: 'failed',
        error: err instanceof Error ? err.message : 'Workflow execution failed',
        executingNodeId: null,
      });
    }
  },

  clearExecution: () =>
    set({
      isExecuting: false,
      executionResults: null,
      executionStatus: 'idle',
      executingNodeId: null,
    }),

  setExecutingNodeId: (nodeId) => set({ executingNodeId: nodeId }),

  loadSavedWorkflows: async (projectId) => {
    try {
      const workflows = await studioService.listStudioWorkflows(projectId);
      set({ savedWorkflows: workflows });
    } catch (err) {
      set({ error: err instanceof Error ? err.message : 'Failed to load workflows' });
    }
  },

  saveCurrentWorkflow: async () => {
    const state = useStudioStore.getState();
    const { currentWorkflowId, currentWorkflowName, currentWorkflowDescription, currentProjectId, workflowGraph } = state;
    if (!workflowGraph) return;

    const data = {
      name: currentWorkflowName,
      description: currentWorkflowDescription,
      project_id: currentProjectId,
      nodes: workflowGraph.nodes,
      edges: workflowGraph.edges,
    };

    try {
      if (currentWorkflowId) {
        await studioService.updateStudioWorkflow(currentWorkflowId, data);
      } else {
        const result = await studioService.saveStudioWorkflow(data);
        set({ currentWorkflowId: result.id });
      }
      await state.loadSavedWorkflows(state.currentProjectId || undefined);
    } catch (err) {
      set({ error: err instanceof Error ? err.message : 'Failed to save workflow' });
    }
  },

  loadWorkflow: (workflowId) => {
    const workflow = useStudioStore.getState().savedWorkflows.find((w) => w.id === workflowId);
    if (!workflow) return;

    set({
      currentWorkflowId: workflow.id,
      currentWorkflowName: workflow.name,
      currentWorkflowDescription: workflow.description,
      currentProjectId: workflow.project_id,
      workflowGraph: {
        nodes: workflow.nodes as WorkflowGraph['nodes'],
        edges: workflow.edges as WorkflowGraph['edges'],
      },
    });
  },

  deleteWorkflow: async (workflowId) => {
    try {
      await studioService.deleteStudioWorkflow(workflowId);
      const state = useStudioStore.getState();
      if (state.currentWorkflowId === workflowId) {
        set({ currentWorkflowId: null, currentWorkflowName: 'Untitled Workflow', currentWorkflowDescription: '' });
      }
      await state.loadSavedWorkflows(state.currentProjectId || undefined);
    } catch (err) {
      set({ error: err instanceof Error ? err.message : 'Failed to delete workflow' });
    }
  },

  setCurrentWorkflowName: (name) => set({ currentWorkflowName: name }),
  setCurrentWorkflowDescription: (desc) => set({ currentWorkflowDescription: desc }),
  setCurrentProjectId: (projectId) => set({ currentProjectId: projectId }),
  newWorkflow: () =>
    set({
      currentWorkflowId: null,
      currentWorkflowName: 'Untitled Workflow',
      currentWorkflowDescription: '',
      workflowGraph: {
        nodes: [
          { id: 'start-1', type: 'start', label: 'Start', position: { x: 0, y: 0 }, data: {}, status: 'idle' },
          { id: 'end-1', type: 'end', label: 'End', position: { x: 0, y: 1 }, data: {}, status: 'idle' },
        ],
        edges: [{ id: 'e-start-end', source: 'start-1', target: 'end-1', label: '' }],
      },
    }),
}));
