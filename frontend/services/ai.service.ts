import { apiClient } from "./api";
import { API_URL, STORAGE_KEYS } from "@/config/constants";
import type {
  ChatRequest,
  ChatResponse,
  ChatStreamChunk,
  ModelListResponse,
  ModelSwitchResponse,
  OllamaStatus,
  Conversation,
} from "@/types/ai";

const AI_BASE = "/ai";

let activeAbortController: AbortController | null = null;

export const aiService = {
  chat: (request: ChatRequest) =>
    apiClient.post<ChatResponse>(`${AI_BASE}/chat`, request),

  chatStream: async function* (request: ChatRequest, signal?: AbortSignal) {
    const token =
      typeof window !== "undefined"
        ? localStorage.getItem(STORAGE_KEYS.AUTH_TOKEN)
        : null;

    const response = await fetch(`${API_URL}${AI_BASE}/chat/stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(request),
      signal,
    });

    if (!response.ok) {
      throw new Error(`Stream request failed: ${response.status}`);
    }

    const reader = response.body?.getReader();
    if (!reader) throw new Error("No reader available");

    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        const trimmed = line.trim();
        if (trimmed.startsWith("data: ")) {
          const data = trimmed.slice(6);
          if (data === "[DONE]") return;
          try {
            yield JSON.parse(data) as ChatStreamChunk;
          } catch {
            // Skip malformed chunks
          }
        }
      }
    }
  },

  startStream: (request: ChatRequest) => {
    activeAbortController = new AbortController();
    return {
      stream: aiService.chatStream(request, activeAbortController.signal),
      signal: activeAbortController.signal,
    };
  },

  stopStream: () => {
    if (activeAbortController) {
      activeAbortController.abort();
      activeAbortController = null;
    }
  },

  getModels: () => apiClient.get<ModelListResponse>(`${AI_BASE}/models`),

  switchModel: (model_name: string) =>
    apiClient.post<ModelSwitchResponse>(`${AI_BASE}/models/switch`, {
      model_name,
    }),

  getStatus: () => apiClient.get<OllamaStatus>(`${AI_BASE}/status`),

  stopGeneration: (conversation_id: string) =>
    apiClient.post(`${AI_BASE}/stop`, null, {
      params: { conversation_id },
    }),

  getConversations: () =>
    apiClient.get<Conversation[]>(`${AI_BASE}/conversations`),

  createConversation: (model?: string) =>
    apiClient.post<Conversation>(`${AI_BASE}/conversations`, null, {
      params: model ? { model } : undefined,
    }),

  getConversation: (id: string) =>
    apiClient.get<Conversation>(`${AI_BASE}/conversations/${id}`),

  deleteConversation: (id: string) =>
    apiClient.delete(`${AI_BASE}/conversations/${id}`),
};
