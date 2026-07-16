import { apiClient } from './api';
import type {
  ArtifactResponse,
  DockerfileResult,
  ComposeResult,
  GitHubActionsResult,
  KubernetesResult,
  ReportResponse,
  TaskListItem,
  ArtifactType,
} from '@/types/deployment';

const DEVOPS_ENDPOINTS = {
  ANALYZE: '/devops/analyze',
  GENERATE: '/devops/generate',
  REPORT: (taskId: string) => `/devops/report/${taskId}`,
  DOCKER: (taskId: string) => `/devops/docker/${taskId}`,
  GITHUB_ACTIONS: (taskId: string) => `/devops/github-actions/${taskId}`,
  KUBERNETES: (taskId: string) => `/devops/kubernetes/${taskId}`,
  TASKS: '/devops/tasks',
  TASK: (taskId: string) => `/devops/tasks/${taskId}`,
};

export const deploymentService = {
  async analyze(
    repositoryId: string,
    projectPath: string = '.',
    description: string = '',
    artifactTypes?: ArtifactType[]
  ): Promise<ArtifactResponse> {
    const response = await apiClient.post(DEVOPS_ENDPOINTS.ANALYZE, {
      repository_id: repositoryId,
      project_path: projectPath,
      description,
      artifact_types: artifactTypes,
    });
    return response.data as any;
  },

  async generate(
    repositoryId: string,
    artifactType: ArtifactType,
    projectPath: string = '.',
    config?: Record<string, unknown>
  ): Promise<ArtifactResponse> {
    const response = await apiClient.post(DEVOPS_ENDPOINTS.GENERATE, {
      repository_id: repositoryId,
      project_path: projectPath,
      artifact_type: artifactType,
      config,
    });
    return response.data as any;
  },

  async getReport(taskId: string): Promise<ReportResponse> {
    const response = await apiClient.get(DEVOPS_ENDPOINTS.REPORT(taskId));
    return response.data as any;
  },

  async getDocker(
    taskId: string
  ): Promise<{
    dockerfile: DockerfileResult | null;
    compose: ComposeResult | null;
    compose_dev: ComposeResult | null;
  }> {
    const response = await apiClient.get(DEVOPS_ENDPOINTS.DOCKER(taskId));
    return response.data as any;
  },

  async getGitHubActions(taskId: string): Promise<GitHubActionsResult> {
    const response = await apiClient.get(DEVOPS_ENDPOINTS.GITHUB_ACTIONS(taskId));
    return response.data as any;
  },

  async getKubernetes(taskId: string): Promise<KubernetesResult> {
    const response = await apiClient.get(DEVOPS_ENDPOINTS.KUBERNETES(taskId));
    return response.data as any;
  },

  async listTasks(status?: string): Promise<TaskListItem[]> {
    const response = await apiClient.get(DEVOPS_ENDPOINTS.TASKS, {
      params: status ? { status } : undefined,
    });
    return response.data as any;
  },

  async getTask(taskId: string): Promise<ArtifactResponse> {
    const response = await apiClient.get(DEVOPS_ENDPOINTS.TASK(taskId));
    return response.data as any;
  },
};
