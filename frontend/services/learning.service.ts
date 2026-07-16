import { apiClient } from './api';
import type {
  ProcessWorkflowRequest,
  ProcessResponse,
  RecommendationRequest,
  FeedbackRequest,
  LearningStats,
  GrowthAnalytics,
  LearningTask,
  Experience,
  Pattern,
  Lesson,
  Recommendation,
} from '@/types/learning';

const LEARNING_ENDPOINTS = {
  PROCESS: '/learning/process',
  PATTERNS: '/learning/patterns',
  EXPERIENCES: '/learning/experiences',
  RECOMMENDATIONS: '/learning/recommendations',
  FEEDBACK: '/learning/feedback',
  STATS: '/learning/stats',
  GROWTH: '/learning/growth',
  TASKS: '/learning/tasks',
};

export const learningService = {
  async processWorkflow(request: ProcessWorkflowRequest): Promise<ProcessResponse> {
    const response = await apiClient.post(LEARNING_ENDPOINTS.PROCESS, request);
    return response.data as any;
  },

  async getPatterns(params?: {
    pattern_type?: string;
    technologies?: string;
    limit?: number;
  }): Promise<Pattern[]> {
    const response = await apiClient.get(LEARNING_ENDPOINTS.PATTERNS, { params });
    return response.data as any;
  },

  async getExperiences(params?: {
    experience_type?: string;
    outcome?: string;
    limit?: number;
  }): Promise<Experience[]> {
    const response = await apiClient.get(LEARNING_ENDPOINTS.EXPERIENCES, { params });
    return response.data as any;
  },

  async getRecommendations(params?: {
    task_type?: string;
    technologies?: string;
  }): Promise<Recommendation[]> {
    const response = await apiClient.get(LEARNING_ENDPOINTS.RECOMMENDATIONS, { params });
    return response.data as any;
  },

  async generateRecommendations(request: RecommendationRequest): Promise<Recommendation[]> {
    const response = await apiClient.post(LEARNING_ENDPOINTS.RECOMMENDATIONS, request);
    return response.data as any;
  },

  async submitFeedback(request: FeedbackRequest): Promise<{ experience_id: string; status: string }> {
    const response = await apiClient.post(LEARNING_ENDPOINTS.FEEDBACK, request);
    return response.data as any;
  },

  async getStats(): Promise<LearningStats> {
    const response = await apiClient.get(LEARNING_ENDPOINTS.STATS);
    return response.data as any;
  },

  async getGrowth(): Promise<GrowthAnalytics> {
    const response = await apiClient.get(LEARNING_ENDPOINTS.GROWTH);
    return response.data as any;
  },

  async listTasks(): Promise<LearningTask[]> {
    const response = await apiClient.get(LEARNING_ENDPOINTS.TASKS);
    return response.data as any;
  },
};
