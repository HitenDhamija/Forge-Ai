import { create } from 'zustand';
import type {
  Experience,
  Pattern,
  Lesson,
  Recommendation,
  LearningStats,
  GrowthAnalytics,
  LearningTask,
  ProcessResponse,
} from '@/types/learning';
import { learningService } from '@/services/learning.service';
import type { FeedbackType } from '@/types/learning';

interface LearningState {
  experiences: Experience[];
  patterns: Pattern[];
  lessons: Lesson[];
  recommendations: Recommendation[];
  stats: LearningStats | null;
  growth: GrowthAnalytics | null;
  tasks: LearningTask[];
  lastProcessResult: ProcessResponse | null;
  isLoading: boolean;
  error: string | null;

  processWorkflow: (params: {
    workflow_id: string;
    repository_id?: string;
    title?: string;
    description?: string;
    outcome?: string;
    files_changed?: string[];
    technologies?: string[];
    context?: Record<string, unknown>;
  }) => Promise<void>;
  fetchExperiences: (params?: {
    experience_type?: string;
    outcome?: string;
    limit?: number;
  }) => Promise<void>;
  fetchPatterns: (params?: {
    pattern_type?: string;
    technologies?: string;
    limit?: number;
  }) => Promise<void>;
  fetchRecommendations: (params?: {
    task_type?: string;
    technologies?: string;
  }) => Promise<void>;
  fetchStats: () => Promise<void>;
  fetchGrowth: () => Promise<void>;
  fetchTasks: () => Promise<void>;
  submitFeedback: (params: {
    experience_id: string;
    feedback_type: FeedbackType;
    rating?: number;
    comment?: string;
  }) => Promise<void>;
  clearError: () => void;
}

export const useLearningStore = create<LearningState>((set) => ({
  experiences: [],
  patterns: [],
  lessons: [],
  recommendations: [],
  stats: null,
  growth: null,
  tasks: [],
  lastProcessResult: null,
  isLoading: false,
  error: null,

  processWorkflow: async (params) => {
    set({ isLoading: true, error: null });
    try {
      const result = await learningService.processWorkflow(params);
      set({ lastProcessResult: result, isLoading: false });
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : 'Failed to process workflow',
        isLoading: false,
      });
    }
  },

  fetchExperiences: async (params) => {
    set({ isLoading: true, error: null });
    try {
      const experiences = await learningService.getExperiences(params);
      set({ experiences, isLoading: false });
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : 'Failed to fetch experiences',
        isLoading: false,
      });
    }
  },

  fetchPatterns: async (params) => {
    set({ isLoading: true, error: null });
    try {
      const patterns = await learningService.getPatterns(params);
      set({ patterns, isLoading: false });
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : 'Failed to fetch patterns',
        isLoading: false,
      });
    }
  },

  fetchRecommendations: async (params) => {
    set({ isLoading: true, error: null });
    try {
      const recommendations = await learningService.getRecommendations(params);
      set({ recommendations, isLoading: false });
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : 'Failed to fetch recommendations',
        isLoading: false,
      });
    }
  },

  fetchStats: async () => {
    set({ isLoading: true, error: null });
    try {
      const stats = await learningService.getStats();
      set({ stats, isLoading: false });
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : 'Failed to fetch stats',
        isLoading: false,
      });
    }
  },

  fetchGrowth: async () => {
    set({ isLoading: true, error: null });
    try {
      const growth = await learningService.getGrowth();
      set({ growth, isLoading: false });
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : 'Failed to fetch growth',
        isLoading: false,
      });
    }
  },

  fetchTasks: async () => {
    set({ isLoading: true, error: null });
    try {
      const tasks = await learningService.listTasks();
      set({ tasks, isLoading: false });
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : 'Failed to fetch tasks',
        isLoading: false,
      });
    }
  },

  submitFeedback: async (params) => {
    set({ isLoading: true, error: null });
    try {
      await learningService.submitFeedback(params);
      set({ isLoading: false });
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : 'Failed to submit feedback',
        isLoading: false,
      });
    }
  },

  clearError: () => set({ error: null }),
}));
