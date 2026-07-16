import { create } from 'zustand';
import type {
  ArtifactResponse,
  DockerfileResult,
  ComposeResult,
  GitHubActionsResult,
  KubernetesResult,
  ProductionScore,
  SecurityValidation,
  DeploymentAnalysis,
  TaskListItem,
  ArtifactType,
} from '@/types/deployment';
import { deploymentService } from '@/services/deployment.service';

interface DeploymentState {
  currentTask: ArtifactResponse | null;
  tasks: TaskListItem[];
  isLoading: boolean;
  error: string | null;

  // Derived state getters
  analysis: DeploymentAnalysis | null;
  security: SecurityValidation | null;
  score: ProductionScore | null;
  dockerfile: DockerfileResult | null;
  compose: ComposeResult | null;
  composeDev: ComposeResult | null;
  githubActions: GitHubActionsResult | null;
  kubernetes: KubernetesResult | null;

  analyze: (
    repositoryId: string,
    projectPath?: string,
    description?: string,
    artifactTypes?: ArtifactType[]
  ) => Promise<void>;
  generate: (
    repositoryId: string,
    artifactType: ArtifactType,
    projectPath?: string
  ) => Promise<void>;
  fetchTask: (taskId: string) => Promise<void>;
  fetchTasks: (status?: string) => Promise<void>;
  fetchDocker: (taskId: string) => Promise<void>;
  fetchGitHubActions: (taskId: string) => Promise<void>;
  fetchKubernetes: (taskId: string) => Promise<void>;
  clearError: () => void;
  clearCurrentTask: () => void;
}

export const useDeploymentStore = create<DeploymentState>((set, get) => ({
  currentTask: null,
  tasks: [],
  isLoading: false,
  error: null,

  get analysis() {
    return get().currentTask?.analysis ?? null;
  },
  get security() {
    return get().currentTask?.security ?? null;
  },
  get score() {
    return get().currentTask?.score ?? null;
  },
  get dockerfile() {
    const task = get().currentTask;
    if (!task) return null;
    return (task.artifacts.dockerfile as DockerfileResult) ?? null;
  },
  get compose() {
    const task = get().currentTask;
    if (!task) return null;
    return (task.artifacts.compose as ComposeResult) ?? null;
  },
  get composeDev() {
    const task = get().currentTask;
    if (!task) return null;
    return (task.artifacts.compose_dev as ComposeResult) ?? null;
  },
  get githubActions() {
    const task = get().currentTask;
    if (!task) return null;
    return (task.artifacts.github_actions as GitHubActionsResult) ?? null;
  },
  get kubernetes() {
    const task = get().currentTask;
    if (!task) return null;
    return (task.artifacts.kubernetes as KubernetesResult) ?? null;
  },

  analyze: async (repositoryId, projectPath = '.', description = '', artifactTypes) => {
    set({ isLoading: true, error: null });
    try {
      const result = await deploymentService.analyze(
        repositoryId,
        projectPath,
        description,
        artifactTypes
      );
      set({ currentTask: result, isLoading: false });
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : 'Failed to run analysis',
        isLoading: false,
      });
    }
  },

  generate: async (repositoryId, artifactType, projectPath = '.') => {
    set({ isLoading: true, error: null });
    try {
      const result = await deploymentService.generate(
        repositoryId,
        artifactType,
        projectPath
      );
      set({ currentTask: result, isLoading: false });
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : 'Failed to generate artifact',
        isLoading: false,
      });
    }
  },

  fetchTask: async (taskId) => {
    set({ isLoading: true, error: null });
    try {
      const result = await deploymentService.getTask(taskId);
      set({ currentTask: result, isLoading: false });
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : 'Failed to fetch task',
        isLoading: false,
      });
    }
  },

  fetchTasks: async (status) => {
    set({ isLoading: true, error: null });
    try {
      const tasks = await deploymentService.listTasks(status);
      set({ tasks, isLoading: false });
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : 'Failed to fetch tasks',
        isLoading: false,
      });
    }
  },

  fetchDocker: async (taskId) => {
    set({ isLoading: true, error: null });
    try {
      const docker = await deploymentService.getDocker(taskId);
      set((state) => ({
        currentTask: state.currentTask
          ? {
              ...state.currentTask,
              artifacts: {
                ...state.currentTask.artifacts,
                dockerfile: docker.dockerfile,
                compose: docker.compose,
                compose_dev: docker.compose_dev,
              },
            }
          : null,
        isLoading: false,
      }));
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : 'Failed to fetch Docker configs',
        isLoading: false,
      });
    }
  },

  fetchGitHubActions: async (taskId) => {
    set({ isLoading: true, error: null });
    try {
      const ga = await deploymentService.getGitHubActions(taskId);
      set((state) => ({
        currentTask: state.currentTask
          ? {
              ...state.currentTask,
              artifacts: {
                ...state.currentTask.artifacts,
                github_actions: ga,
              },
            }
          : null,
        isLoading: false,
      }));
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : 'Failed to fetch GitHub Actions',
        isLoading: false,
      });
    }
  },

  fetchKubernetes: async (taskId) => {
    set({ isLoading: true, error: null });
    try {
      const k8s = await deploymentService.getKubernetes(taskId);
      set((state) => ({
        currentTask: state.currentTask
          ? {
              ...state.currentTask,
              artifacts: {
                ...state.currentTask.artifacts,
                kubernetes: k8s,
              },
            }
          : null,
        isLoading: false,
      }));
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : 'Failed to fetch Kubernetes manifests',
        isLoading: false,
      });
    }
  },

  clearError: () => set({ error: null }),
  clearCurrentTask: () => set({ currentTask: null }),
}));
