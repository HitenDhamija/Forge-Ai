import { apiClient } from './api';
import type {
  AgentInfo,
  AgentMetrics,
  TaskInfo,
  TaskRequest,
} from '@/types/agents';

const AGENT_ENDPOINTS = {
  BASE: '/agents',
  TASKS: '/agents/tasks',
  METRICS: '/agents/metrics/overview',
};

export const agentService = {
  async listAgents(): Promise<AgentInfo[]> {
    const response = await apiClient.get<any>('/agents');
    const data = response.data?.data ?? response.data;
    return Array.isArray(data) ? data : [];
  },

  async getAgent(agentId: string): Promise<AgentInfo> {
    const response = await apiClient.get<any>(`${AGENT_ENDPOINTS.BASE}/${agentId}`);
    return response.data?.data ?? response.data;
  },

  async createTask(request: TaskRequest): Promise<TaskInfo> {
    const response = await apiClient.post<any>(AGENT_ENDPOINTS.TASKS, {
      agent_type: request.agent_type,
      task_description: request.task_description || request.description,
      context: request.context,
    });
    const raw = response.data?.data ?? response.data;
    // Map backend response fields to frontend TaskInfo shape
    return {
      id: raw.id,
      title: raw.title || raw.task_description?.slice(0, 50) || 'Agent Task',
      description: raw.task_description || raw.description || '',
      status: raw.status || 'queued',
      priority: raw.priority || 'medium',
      agent_type: raw.agent_type || request.agent_type,
      steps: raw.steps || [],
      context: raw.context || {},
      result: raw.result,
      error: raw.error,
      created_at: raw.created_at || new Date().toISOString(),
      updated_at: raw.updated_at || new Date().toISOString(),
    };
  },

  async getTask(taskId: string): Promise<TaskInfo> {
    const response = await apiClient.get<any>(`${AGENT_ENDPOINTS.TASKS}/${taskId}`);
    return response.data?.data ?? response.data;
  },

  async cancelTask(taskId: string): Promise<TaskInfo> {
    const response = await apiClient.post<any>(
      `${AGENT_ENDPOINTS.TASKS}/${taskId}/cancel`
    );
    return response.data?.data ?? response.data;
  },

  async listTasks(filters?: {
    status?: string;
    agent_type?: string;
  }): Promise<TaskInfo[]> {
    const response = await apiClient.get<any>(`${AGENT_ENDPOINTS.TASKS}/list`, {
      params: filters,
    });
    const data = response.data?.data ?? response.data;
    return Array.isArray(data) ? data : [];
  },

  async getMetrics(): Promise<AgentMetrics> {
    const response = await apiClient.get<any>(AGENT_ENDPOINTS.METRICS);
    return response.data?.data ?? response.data;
  },
};
