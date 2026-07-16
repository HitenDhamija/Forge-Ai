import { create } from "zustand";
import type { ModelInfo, OllamaStatus } from "@/types/ai";

interface AIState {
  activeModel: string | null;
  ollamaConnected: boolean;
  ollamaVersion: string | null;
  modelsCount: number;
  runningModels: string[];
  availableModels: ModelInfo[];
  isLoading: boolean;
  isGenerating: boolean;
  error: string | null;
}

interface AIActions {
  setActiveModel: (model: string) => void;
  setOllamaStatus: (status: OllamaStatus) => void;
  setAvailableModels: (models: ModelInfo[]) => void;
  setLoading: (loading: boolean) => void;
  setGenerating: (generating: boolean) => void;
  setError: (error: string | null) => void;
  clearError: () => void;
}

type AIStore = AIState & AIActions;

export const useAIStore = create<AIStore>()((set) => ({
  activeModel: null,
  ollamaConnected: false,
  ollamaVersion: null,
  modelsCount: 0,
  runningModels: [],
  availableModels: [],
  isLoading: false,
  isGenerating: false,
  error: null,

  setActiveModel: (model) => set({ activeModel: model }),

  setOllamaStatus: (status) =>
    set({
      ollamaConnected: status.connected,
      ollamaVersion: status.version,
      modelsCount: status.models_count,
      runningModels: status.running_models,
    }),

  setAvailableModels: (models) => set({ availableModels: models }),

  setLoading: (loading) => set({ isLoading: loading }),

  setGenerating: (generating) => set({ isGenerating: generating }),

  setError: (error) => set({ error }),

  clearError: () => set({ error: null }),
}));
