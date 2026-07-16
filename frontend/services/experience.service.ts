import { apiClient } from './api';
import type {
  Notification,
  Activity,
  SearchResult,
  SettingDefinition,
  OnboardingStep,
  OnboardingState,
  Tutorial,
  CommandPaletteItem,
  KeyboardShortcut,
} from '@/types/experience';

const EXPERIENCE_ENDPOINTS = {
  NOTIFICATIONS: '/experience/notifications',
  NOTIFICATION: (id: string) => `/experience/notifications/${id}`,
  NOTIFICATIONS_READ_ALL: '/experience/notifications/read-all',
  UNREAD_COUNT: '/experience/notifications/unread-count',
  ACTIVITY: '/experience/activity',
  ACTIVITY_ENTITY: (type: string, id: string) => `/experience/activity/entity/${type}/${id}`,
  SEARCH: '/experience/search',
  SEARCH_RECENT: '/experience/search/recent',
  SEARCH_POPULAR: '/experience/search/popular',
  SETTINGS: '/experience/settings',
  SETTINGS_RESET: '/experience/settings/reset',
  ONBOARDING_STEPS: '/experience/onboarding/steps',
  ONBOARDING_STATE: '/experience/onboarding/state',
  ONBOARDING_STEP: (id: string) => `/experience/onboarding/step/${id}`,
  ONBOARDING_SKIP: '/experience/onboarding/skip',
  TUTORIALS: '/experience/tutorials',
  TUTORIAL: (id: string) => `/experience/tutorials/${id}`,
  COMMAND_PALETTE: '/experience/command-palette',
  SHORTCUTS: '/experience/shortcuts',
};

export const experienceService = {
  // Notifications
  async listNotifications(userId?: string, status?: string, limit?: number): Promise<Notification[]> {
    const params = new URLSearchParams();
    if (userId) params.set('user_id', userId);
    if (status) params.set('status', status);
    if (limit) params.set('limit', limit.toString());
    const query = params.toString();
    const url = query ? `${EXPERIENCE_ENDPOINTS.NOTIFICATIONS}?${query}` : EXPERIENCE_ENDPOINTS.NOTIFICATIONS;
    const { data } = await apiClient.get(url);
    return data as any;
  },

  async createNotification(data: Partial<Notification>): Promise<Notification> {
    const { data: result } = await apiClient.post(EXPERIENCE_ENDPOINTS.NOTIFICATIONS, data);
    return result as any;
  },

  async markRead(notificationId: string): Promise<void> {
    await apiClient.put(EXPERIENCE_ENDPOINTS.NOTIFICATION(notificationId) + '/read');
  },

  async markAllRead(userId?: string): Promise<{ marked_read: number }> {
    const { data } = await apiClient.put(EXPERIENCE_ENDPOINTS.NOTIFICATIONS_READ_ALL, { user_id: userId });
    return data as any;
  },

  async getUnreadCount(): Promise<{ count: number }> {
    const { data } = await apiClient.get(EXPERIENCE_ENDPOINTS.UNREAD_COUNT);
    return data as any;
  },

  async deleteNotification(notificationId: string): Promise<void> {
    await apiClient.delete(EXPERIENCE_ENDPOINTS.NOTIFICATION(notificationId));
  },

  // Activity
  async listActivity(limit?: number, type?: string): Promise<Activity[]> {
    const params = new URLSearchParams();
    if (limit) params.set('limit', limit.toString());
    if (type) params.set('type', type);
    const query = params.toString();
    const url = query ? `${EXPERIENCE_ENDPOINTS.ACTIVITY}?${query}` : EXPERIENCE_ENDPOINTS.ACTIVITY;
    const { data } = await apiClient.get(url);
    return data as any;
  },

  async logActivity(data: Partial<Activity>): Promise<Activity> {
    const { data: result } = await apiClient.post(EXPERIENCE_ENDPOINTS.ACTIVITY, data);
    return result as any;
  },

  async getEntityActivity(entityType: string, entityId: string): Promise<Activity[]> {
    const { data } = await apiClient.get(EXPERIENCE_ENDPOINTS.ACTIVITY_ENTITY(entityType, entityId));
    return data as any;
  },

  // Search
  async search(query: string, types?: string[], limit?: number): Promise<SearchResult[]> {
    const params = new URLSearchParams({ q: query });
    if (types) params.set('types', types.join(','));
    if (limit) params.set('limit', limit.toString());
    const { data } = await apiClient.get(`${EXPERIENCE_ENDPOINTS.SEARCH}?${params.toString()}`);
    return data as any;
  },

  async getRecentSearches(): Promise<Array<{ query: string; timestamp: string }>> {
    const { data } = await apiClient.get(EXPERIENCE_ENDPOINTS.SEARCH_RECENT);
    return data as any;
  },

  async getPopularSearches(): Promise<Array<{ query: string; count: number }>> {
    const { data } = await apiClient.get(EXPERIENCE_ENDPOINTS.SEARCH_POPULAR);
    return data as any;
  },

  // Settings
  async getSettings(category?: string): Promise<Record<string, SettingDefinition>> {
    const params = category ? `?category=${category}` : '';
    const { data } = await apiClient.get(`${EXPERIENCE_ENDPOINTS.SETTINGS}${params}`);
    return data as any;
  },

  async getSetting(key: string): Promise<SettingDefinition> {
    const { data } = await apiClient.get(`${EXPERIENCE_ENDPOINTS.SETTINGS}/${key}`);
    return data as any;
  },

  async updateSetting(key: string, value: string): Promise<void> {
    await apiClient.put(EXPERIENCE_ENDPOINTS.SETTINGS, { key, value });
  },

  async resetSettings(category?: string): Promise<void> {
    const params = category ? `?category=${category}` : '';
    await apiClient.post(`${EXPERIENCE_ENDPOINTS.SETTINGS_RESET}${params}`);
  },

  // Onboarding
  async getOnboardingSteps(): Promise<OnboardingStep[]> {
    const { data } = await apiClient.get(EXPERIENCE_ENDPOINTS.ONBOARDING_STEPS);
    return data as any;
  },

  async getOnboardingState(): Promise<OnboardingState> {
    const { data } = await apiClient.get(EXPERIENCE_ENDPOINTS.ONBOARDING_STATE);
    return data as any;
  },

  async completeStep(stepId: string): Promise<void> {
    await apiClient.put(EXPERIENCE_ENDPOINTS.ONBOARDING_STEP(stepId));
  },

  async skipOnboarding(): Promise<void> {
    await apiClient.post(EXPERIENCE_ENDPOINTS.ONBOARDING_SKIP);
  },

  // Tutorials
  async listTutorials(): Promise<Tutorial[]> {
    const { data } = await apiClient.get(EXPERIENCE_ENDPOINTS.TUTORIALS);
    return data as any;
  },

  async getTutorial(tutorialId: string): Promise<Tutorial> {
    const { data } = await apiClient.get(EXPERIENCE_ENDPOINTS.TUTORIAL(tutorialId));
    return data as any;
  },

  // Command Palette
  async getCommandPaletteItems(): Promise<CommandPaletteItem[]> {
    const { data } = await apiClient.get(EXPERIENCE_ENDPOINTS.COMMAND_PALETTE);
    return data as any;
  },

  async getKeyboardShortcuts(): Promise<Record<string, KeyboardShortcut[]>> {
    const { data } = await apiClient.get(EXPERIENCE_ENDPOINTS.SHORTCUTS);
    return data as any;
  },
};
