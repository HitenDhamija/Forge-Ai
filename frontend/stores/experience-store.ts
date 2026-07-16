import { create } from 'zustand';
import { experienceService } from '@/services/experience.service';
import type { Notification, Activity, SearchResult, SettingDefinition, OnboardingState, CommandPaletteItem } from '@/types/experience';

interface ExperienceState {
  // Notifications
  notifications: Notification[];
  unreadCount: number;

  // Activity
  activities: Activity[];

  // Search
  searchResults: SearchResult[];
  recentSearches: Array<{ query: string; timestamp: string }>;
  popularSearches: Array<{ query: string; count: number }>;

  // Settings
  settings: Record<string, SettingDefinition>;

  // Onboarding
  onboardingState: OnboardingState | null;

  // Command Palette
  commandPaletteItems: CommandPaletteItem[];
  isCommandPaletteOpen: boolean;

  // UI State
  isSearchOpen: boolean;
  isNotificationOpen: boolean;
  isLoading: boolean;
  error: string | null;

  // Actions
  fetchNotifications: () => Promise<void>;
  markNotificationRead: (id: string) => Promise<void>;
  markAllNotificationsRead: () => Promise<void>;
  fetchUnreadCount: () => Promise<void>;
  createNotification: (data: Partial<Notification>) => Promise<void>;

  fetchActivities: (limit?: number) => Promise<void>;

  search: (query: string) => Promise<void>;
  clearSearch: () => void;
  fetchRecentSearches: () => Promise<void>;
  fetchPopularSearches: () => Promise<void>;

  fetchSettings: (category?: string) => Promise<void>;
  updateSetting: (key: string, value: string) => Promise<void>;

  fetchOnboardingState: () => Promise<void>;
  completeOnboardingStep: (stepId: string) => Promise<void>;
  skipOnboarding: () => Promise<void>;

  fetchCommandPaletteItems: () => Promise<void>;
  openCommandPalette: () => void;
  closeCommandPalette: () => void;

  toggleSearch: () => void;
  toggleNotifications: () => void;
}

export const useExperienceStore = create<ExperienceState>((set, get) => ({
  // State
  notifications: [],
  unreadCount: 0,
  activities: [],
  searchResults: [],
  recentSearches: [],
  popularSearches: [],
  settings: {},
  onboardingState: null,
  commandPaletteItems: [],
  isCommandPaletteOpen: false,
  isSearchOpen: false,
  isNotificationOpen: false,
  isLoading: false,
  error: null,

  // Notification Actions
  fetchNotifications: async () => {
    set({ isLoading: true, error: null });
    try {
      const notifications = await experienceService.listNotifications();
      set({ notifications, isLoading: false });
    } catch (error) {
      set({ error: 'Failed to fetch notifications', isLoading: false });
    }
  },

  markNotificationRead: async (id: string) => {
    try {
      await experienceService.markRead(id);
      const notifications = get().notifications.map(n =>
        n.id === id ? { ...n, read_at: new Date().toISOString() } : n
      );
      set({
        notifications,
        unreadCount: notifications.filter(n => !n.read_at).length,
      });
    } catch (error) {
      set({ error: 'Failed to mark notification as read' });
    }
  },

  markAllNotificationsRead: async () => {
    try {
      await experienceService.markAllRead();
      const notifications = get().notifications.map(n => ({ ...n, read_at: new Date().toISOString() }));
      set({ notifications, unreadCount: 0 });
    } catch (error) {
      set({ error: 'Failed to mark all notifications as read' });
    }
  },

  fetchUnreadCount: async () => {
    try {
      const { count } = await experienceService.getUnreadCount();
      set({ unreadCount: count });
    } catch (error) {
      set({ error: 'Failed to fetch unread count' });
    }
  },

  createNotification: async (data: Partial<Notification>) => {
    try {
      const notification = await experienceService.createNotification(data);
      set({ notifications: [notification, ...get().notifications] });
    } catch (error) {
      set({ error: 'Failed to create notification' });
    }
  },

  // Activity Actions
  fetchActivities: async (limit: number = 20) => {
    set({ isLoading: true, error: null });
    try {
      const activities = await experienceService.listActivity(limit);
      set({ activities, isLoading: false });
    } catch (error) {
      set({ error: 'Failed to fetch activities', isLoading: false });
    }
  },

  // Search Actions
  search: async (query: string) => {
    if (!query.trim()) {
      set({ searchResults: [] });
      return;
    }
    set({ isLoading: true, error: null });
    try {
      const results = await experienceService.search(query);
      set({ searchResults: results, isLoading: false });
    } catch (error) {
      set({ error: 'Failed to perform search', isLoading: false });
    }
  },

  clearSearch: () => {
    set({ searchResults: [] });
  },

  fetchRecentSearches: async () => {
    try {
      const recentSearches = await experienceService.getRecentSearches();
      set({ recentSearches });
    } catch (error) {
      set({ error: 'Failed to fetch recent searches' });
    }
  },

  fetchPopularSearches: async () => {
    try {
      const popularSearches = await experienceService.getPopularSearches();
      set({ popularSearches });
    } catch (error) {
      set({ error: 'Failed to fetch popular searches' });
    }
  },

  // Settings Actions
  fetchSettings: async (category?: string) => {
    set({ isLoading: true, error: null });
    try {
      const settings = await experienceService.getSettings(category);
      set({ settings, isLoading: false });
    } catch (error) {
      set({ error: 'Failed to fetch settings', isLoading: false });
    }
  },

  updateSetting: async (key: string, value: string) => {
    try {
      await experienceService.updateSetting(key, value);
      const settings = { ...get().settings };
      if (settings[key]) {
        settings[key] = { ...settings[key], value };
      }
      set({ settings });
    } catch (error) {
      set({ error: 'Failed to update setting' });
    }
  },

  // Onboarding Actions
  fetchOnboardingState: async () => {
    set({ isLoading: true, error: null });
    try {
      const onboardingState = await experienceService.getOnboardingState();
      set({ onboardingState, isLoading: false });
    } catch (error) {
      set({ error: 'Failed to fetch onboarding state', isLoading: false });
    }
  },

  completeOnboardingStep: async (stepId: string) => {
    try {
      await experienceService.completeStep(stepId);
      const onboardingState = get().onboardingState;
      if (onboardingState) {
        const completedSteps = onboardingState.completed_steps + 1;
        set({
          onboardingState: {
            ...onboardingState,
            completed_steps: completedSteps,
            current_step: stepId,
            is_complete: completedSteps === onboardingState.total_steps,
            progress: (completedSteps / onboardingState.total_steps) * 100,
          },
        });
      }
    } catch (error) {
      set({ error: 'Failed to complete onboarding step' });
    }
  },

  skipOnboarding: async () => {
    try {
      await experienceService.skipOnboarding();
      set({ onboardingState: null });
    } catch (error) {
      set({ error: 'Failed to skip onboarding' });
    }
  },

  // Command Palette Actions
  fetchCommandPaletteItems: async () => {
    try {
      const commandPaletteItems = await experienceService.getCommandPaletteItems();
      set({ commandPaletteItems });
    } catch (error) {
      set({ error: 'Failed to fetch command palette items' });
    }
  },

  openCommandPalette: () => {
    set({ isCommandPaletteOpen: true });
  },

  closeCommandPalette: () => {
    set({ isCommandPaletteOpen: false });
  },

  // UI Actions
  toggleSearch: () => {
    set({ isSearchOpen: !get().isSearchOpen });
  },

  toggleNotifications: () => {
    set({ isNotificationOpen: !get().isNotificationOpen });
  },
}));
