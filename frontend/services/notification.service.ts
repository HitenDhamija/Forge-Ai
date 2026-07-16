import { apiClient } from "./api";

const NOTIFY_BASE = "";

export const notificationService = {
  getPreferences: async () => {
    const { data } = await apiClient.get<any>(`${NOTIFY_BASE}/notifications/preferences`);
    return data.data || data;
  },

  updatePreferences: async (preferences: Record<string, boolean>) => {
    const { data } = await apiClient.put<any>(`${NOTIFY_BASE}/notifications/preferences`, { preferences });
    return data.data || data;
  },

  getSMTPStatus: async () => {
    const { data } = await apiClient.get<any>(`${NOTIFY_BASE}/notifications/smtp-status`);
    return data.data || data;
  },

  sendTestEmail: async (to: string) => {
    const { data } = await apiClient.post<any>(`${NOTIFY_BASE}/notifications/test-email`, { to });
    return data;
  },
};
