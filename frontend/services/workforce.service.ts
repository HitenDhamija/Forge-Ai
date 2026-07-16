import { apiClient } from './api';
import type {
  AgentInfo,
  AgentStatusSummary,
  WorkflowEvent,
} from '@/types/workforce';

const WORKFORCE_ENDPOINTS = {
  BASE: '/workforce',
  STATUS: '/workforce/status',
  EVENTS: '/workforce/events/recent',
};

export const workforceService = {
  async listAgents(): Promise<AgentInfo[]> {
    const response = await apiClient.get(WORKFORCE_ENDPOINTS.BASE);
    return response.data as any;
  },

  async getAgent(agentId: string): Promise<AgentInfo> {
    const response = await apiClient.get(
      `${WORKFORCE_ENDPOINTS.BASE}/${agentId}`
    );
    return response.data as any;
  },

  async getAgentsByRole(role: string): Promise<AgentInfo[]> {
    const response = await apiClient.get(
      `${WORKFORCE_ENDPOINTS.BASE}/role/${role}`
    );
    return response.data as any;
  },

  async getStatusSummary(): Promise<AgentStatusSummary> {
    const response = await apiClient.get(WORKFORCE_ENDPOINTS.STATUS);
    return response.data as any;
  },

  async registerAgent(agentData: Record<string, unknown>): Promise<{ agent_id: string }> {
    const response = await apiClient.post(
      `${WORKFORCE_ENDPOINTS.BASE}/register`,
      agentData
    );
    return response.data as any;
  },

  async sendHeartbeat(agentId: string): Promise<void> {
    await apiClient.post(
      `${WORKFORCE_ENDPOINTS.BASE}/${agentId}/heartbeat`
    );
  },

  async updateAgentStatus(
    agentId: string,
    status: string
  ): Promise<void> {
    await apiClient.post(
      `${WORKFORCE_ENDPOINTS.BASE}/${agentId}/status`,
      { status }
    );
  },

  async getRecentEvents(limit?: number): Promise<WorkflowEvent[]> {
    const response = await apiClient.get(WORKFORCE_ENDPOINTS.EVENTS, {
      params: { limit },
    });
    return response.data as any;
  },

  async processWorkflow(
    workflowId: string,
    workflowData: Record<string, unknown>
  ): Promise<Record<string, unknown>> {
    const response = await apiClient.post(
      `${WORKFORCE_ENDPOINTS.BASE}/workflow/${workflowId}/process`,
      workflowData
    );
    return response.data as any;
  },
};
