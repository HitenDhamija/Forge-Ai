import { apiClient } from './api';
import type {
  ExecutionSummary,
  WorkflowInfo,
  WorkflowRequest,
} from '@/types/workflows';

const WORKFLOW_ENDPOINTS = {
  BASE: '/workflows',
};

function unwrap<T>(response: any): T {
  return response.data?.data ?? response.data;
}

export const workflowService = {
  async createWorkflow(request: WorkflowRequest): Promise<WorkflowInfo> {
    const response = await apiClient.post<any>(WORKFLOW_ENDPOINTS.BASE, request);
    return unwrap<WorkflowInfo>(response);
  },

  async listWorkflows(filters?: {
    status?: string;
    project_id?: string;
  }): Promise<WorkflowInfo[]> {
    const response = await apiClient.get<any>(WORKFLOW_ENDPOINTS.BASE, {
      params: filters,
    });
    const data = response.data?.data ?? response.data;
    return Array.isArray(data) ? data : [];
  },

  async getWorkflow(workflowId: string): Promise<WorkflowInfo> {
    const response = await apiClient.get<any>(
      `${WORKFLOW_ENDPOINTS.BASE}/${workflowId}`
    );
    return unwrap<WorkflowInfo>(response);
  },

  async approveWorkflow(workflowId: string): Promise<WorkflowInfo> {
    const response = await apiClient.post<any>(
      `${WORKFLOW_ENDPOINTS.BASE}/${workflowId}/approve`
    );
    return unwrap<WorkflowInfo>(response);
  },

  async startWorkflow(workflowId: string): Promise<WorkflowInfo> {
    const response = await apiClient.post<any>(
      `${WORKFLOW_ENDPOINTS.BASE}/${workflowId}/start`
    );
    return unwrap<WorkflowInfo>(response);
  },

  async pauseWorkflow(workflowId: string): Promise<WorkflowInfo> {
    const response = await apiClient.post<any>(
      `${WORKFLOW_ENDPOINTS.BASE}/${workflowId}/pause`
    );
    return unwrap<WorkflowInfo>(response);
  },

  async resumeWorkflow(workflowId: string): Promise<WorkflowInfo> {
    const response = await apiClient.post<any>(
      `${WORKFLOW_ENDPOINTS.BASE}/${workflowId}/resume`
    );
    return unwrap<WorkflowInfo>(response);
  },

  async cancelWorkflow(workflowId: string): Promise<WorkflowInfo> {
    const response = await apiClient.post<any>(
      `${WORKFLOW_ENDPOINTS.BASE}/${workflowId}/cancel`
    );
    return unwrap<WorkflowInfo>(response);
  },

  async getExecutionSummary(
    workflowId: string
  ): Promise<ExecutionSummary> {
    const response = await apiClient.get<any>(
      `${WORKFLOW_ENDPOINTS.BASE}/${workflowId}/summary`
    );
    return unwrap<ExecutionSummary>(response);
  },

  async updateWorkflow(
    workflowId: string,
    data: { title?: string; description?: string; tasks?: { title: string; description: string; priority?: string }[] }
  ): Promise<WorkflowInfo> {
    const response = await apiClient.put<any>(
      `${WORKFLOW_ENDPOINTS.BASE}/${workflowId}`,
      data
    );
    return unwrap<WorkflowInfo>(response);
  },

  async deleteWorkflow(workflowId: string): Promise<void> {
    await apiClient.delete(`${WORKFLOW_ENDPOINTS.BASE}/${workflowId}`);
  },
};
