import { apiClient } from './api';
import { API_URL } from '@/config/constants';
import type {
  WorkflowGraph,
  NodeTemplate,
  PromptTemplate,
  PromptTestResult,
  ReplayState,
  ReplayEvent,
  AgentDetail,
  AgentPerformance,
  WorkspaceOverview,
  WorkspaceItem,
} from '@/types/studio';

const STUDIO_ENDPOINTS = {
  WORKFLOWS: '/studio/workflows',
  WORKFLOWS_LIST: '/studio/workflows/list',
  WORKFLOWS_SAVE: '/studio/workflows/save',
  WORKFLOW_GRAPH: (id: string) => `/studio/workflows/${id}/graph`,
  WORKFLOW_UPDATE: (id: string) => `/studio/workflows/${id}`,
  WORKFLOW_DELETE: (id: string) => `/studio/workflows/${id}`,
  NODE_TEMPLATES: '/studio/workflows/node-templates',
  VALIDATE: '/studio/workflows/validate',
  EXECUTE: '/studio/workflows/execute',
  PROMPTS: '/studio/prompts',
  PROMPT: (id: string) => `/studio/prompts/${id}`,
  PROMPT_HISTORY: (id: string) => `/studio/prompts/${id}/history`,
  PROMPT_TEST: (id: string) => `/studio/prompts/${id}/test`,
  PROMPT_ROLLBACK: (id: string) => `/studio/prompts/${id}/rollback`,
  REPLAY: (id: string) => `/studio/replay/${id}`,
  REPLAY_EVENTS: (id: string) => `/studio/replay/${id}/events`,
  REPLAY_STEP: (id: string) => `/studio/replay/${id}/step-forward`,
  AGENTS: '/studio/agents',
  AGENT: (id: string) => `/studio/agents/${id}`,
  AGENT_CONFIG: (id: string) => `/studio/agents/${id}/config`,
  AGENT_PERFORMANCE: (id: string) => `/studio/agents/${id}/performance`,
  AGENT_TEST: (id: string) => `/studio/agents/${id}/test`,
  WORKSPACE: '/studio/workspace',
  WORKSPACE_SEARCH: '/studio/workspace/search',
  WORKSPACE_RECENT: '/studio/workspace/recent',
  WORKSPACE_BOOKMARKS: '/studio/workspace/bookmarks',
};

export const studioService = {
  // Workflow Builder
  async getWorkflowGraph(workflowId: string): Promise<WorkflowGraph> {
    const response = await apiClient.get(STUDIO_ENDPOINTS.WORKFLOW_GRAPH(workflowId));
    return response.data as any;
  },

  async getNodeTemplates(): Promise<NodeTemplate[]> {
    const response = await apiClient.get(STUDIO_ENDPOINTS.NODE_TEMPLATES);
    return response.data as any;
  },

  async validateWorkflow(nodes: unknown[], edges: unknown[]): Promise<Record<string, unknown>> {
    const response = await apiClient.post(STUDIO_ENDPOINTS.VALIDATE, { nodes, edges });
    return response.data as any;
  },

  async listStudioWorkflows(projectId?: string): Promise<Array<{
    id: string;
    name: string;
    description: string;
    project_id: string | null;
    nodes: unknown[];
    edges: unknown[];
    created_at: string;
    updated_at: string;
  }>> {
    const params = projectId ? { project_id: projectId } : {};
    const response = await apiClient.get(STUDIO_ENDPOINTS.WORKFLOWS_LIST, { params });
    return response.data as any;
  },

  async saveStudioWorkflow(data: {
    name: string;
    description?: string;
    project_id?: string | null;
    nodes: unknown[];
    edges: unknown[];
  }): Promise<{ id: string }> {
    const response = await apiClient.post(STUDIO_ENDPOINTS.WORKFLOWS_SAVE, data);
    return response.data as any;
  },

  async updateStudioWorkflow(workflowId: string, data: {
    name: string;
    description?: string;
    project_id?: string | null;
    nodes: unknown[];
    edges: unknown[];
  }): Promise<void> {
    await apiClient.put(STUDIO_ENDPOINTS.WORKFLOW_UPDATE(workflowId), data);
  },

  async deleteStudioWorkflow(workflowId: string): Promise<void> {
    await apiClient.delete(STUDIO_ENDPOINTS.WORKFLOW_DELETE(workflowId));
  },

  async *executeWorkflowStream(
    nodes: unknown[],
    edges: unknown[],
    inputs?: Record<string, unknown>
  ): AsyncGenerator<{
    type: 'node_start' | 'node_complete' | 'node_error' | 'workflow_complete';
    node_id?: string;
    node_type?: string;
    label?: string;
    status?: string;
    output?: Record<string, unknown>;
    duration_ms?: number;
    error?: string;
    llm_model?: string;
    tokens_used?: number;
    execution_id?: string;
    total_duration_ms?: number;
    nodes_executed?: number;
    final_output?: Record<string, unknown>;
  }> {
    const response = await fetch(`${API_URL}/studio/workflows/execute`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ nodes, edges, inputs: inputs || {} }),
    });

    if (!response.ok) {
      throw new Error(`Workflow execution failed: ${response.statusText}`);
    }

    const reader = response.body?.getReader();
    if (!reader) throw new Error('No response body');

    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const event = JSON.parse(line.slice(6));
            yield event;
          } catch {
            // skip malformed lines
          }
        }
      }
    }
  },

  // Prompt Studio
  async listPrompts(): Promise<PromptTemplate[]> {
    const response = await apiClient.get(STUDIO_ENDPOINTS.PROMPTS);
    return response.data as any;
  },

  async getPrompt(promptId: string): Promise<PromptTemplate> {
    const response = await apiClient.get(STUDIO_ENDPOINTS.PROMPT(promptId));
    return response.data as any;
  },

  async createPrompt(data: {
    name: string;
    description?: string;
    content: string;
    variables?: string[];
    tags?: string[];
  }): Promise<string> {
    const response = await apiClient.post(STUDIO_ENDPOINTS.PROMPTS, data);
    return response.data.prompt_id;
  },

  async updatePrompt(promptId: string, content: string, comment: string): Promise<number> {
    const response = await apiClient.put(STUDIO_ENDPOINTS.PROMPT(promptId), { content, comment });
    return parseInt(response.data.version);
  },

  async testPrompt(promptId: string, model: string, inputVars: Record<string, string>): Promise<PromptTestResult> {
    const response = await apiClient.post(STUDIO_ENDPOINTS.PROMPT_TEST(promptId), { model, input_vars: inputVars });
    return response.data as any;
  },

  async getPromptHistory(promptId: string): Promise<{ version: number; created_by: string; created_at: string; comment: string }[]> {
    const response = await apiClient.get(STUDIO_ENDPOINTS.PROMPT_HISTORY(promptId));
    return response.data as any;
  },

  async rollbackPrompt(promptId: string, version: number): Promise<void> {
    await apiClient.post(STUDIO_ENDPOINTS.PROMPT_ROLLBACK(promptId), { version });
  },

  // Replay
  async getReplay(executionId: string): Promise<ReplayState> {
    const response = await apiClient.get(STUDIO_ENDPOINTS.REPLAY(executionId));
    return response.data as any;
  },

  async getReplayEvents(executionId: string): Promise<ReplayEvent[]> {
    const response = await apiClient.get(STUDIO_ENDPOINTS.REPLAY_EVENTS(executionId));
    return response.data as any;
  },

  async stepForward(executionId: string): Promise<ReplayEvent | null> {
    const response = await apiClient.post(STUDIO_ENDPOINTS.REPLAY_STEP(executionId));
    return response.data as any;
  },

  // Agent Playground
  async listAgents(): Promise<AgentDetail[]> {
    const response = await apiClient.get(STUDIO_ENDPOINTS.AGENTS);
    return response.data as any;
  },

  async getAgent(agentId: string): Promise<AgentDetail> {
    const response = await apiClient.get(STUDIO_ENDPOINTS.AGENT(agentId));
    return response.data as any;
  },

  async updateAgentConfig(agentId: string, config: Record<string, unknown>): Promise<void> {
    await apiClient.put(STUDIO_ENDPOINTS.AGENT_CONFIG(agentId), config);
  },

  async getAgentPerformance(agentId: string): Promise<AgentPerformance> {
    const response = await apiClient.get(STUDIO_ENDPOINTS.AGENT_PERFORMANCE(agentId));
    return response.data as any;
  },

  async testAgent(agentId: string, prompt: string, repositoryId?: string): Promise<Record<string, unknown>> {
    const response = await apiClient.post(STUDIO_ENDPOINTS.AGENT_TEST(agentId), { prompt, repository_id: repositoryId });
    return response.data as any;
  },

  // Workspace
  async getWorkspace(): Promise<WorkspaceOverview> {
    const response = await apiClient.get(STUDIO_ENDPOINTS.WORKSPACE);
    return response.data as any;
  },

  async searchWorkspace(query: string, types?: string[]): Promise<WorkspaceItem[]> {
    const response = await apiClient.get(STUDIO_ENDPOINTS.WORKSPACE_SEARCH, {
      params: { query, types: types?.join(',') },
    });
    return response.data as any;
  },

  async getRecentItems(limit?: number): Promise<WorkspaceItem[]> {
    const response = await apiClient.get(STUDIO_ENDPOINTS.WORKSPACE_RECENT, { params: { limit } });
    return response.data as any;
  },

  async getBookmarks(): Promise<WorkspaceItem[]> {
    const response = await apiClient.get(STUDIO_ENDPOINTS.WORKSPACE_BOOKMARKS);
    return response.data as any;
  },
};
