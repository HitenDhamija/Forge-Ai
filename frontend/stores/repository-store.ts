import { create } from "zustand";
import type {
  RepositoryInfo,
  AnalysisResult,
  SemanticGraph,
} from "@/types/repository";

interface RepositoryState {
  repositories: RepositoryInfo[];
  selectedRepository: RepositoryInfo | null;
  analysisResult: AnalysisResult | null;
  semanticGraph: SemanticGraph | null;
  isLoading: boolean;
  isAnalyzing: boolean;
  isImporting: boolean;
  error: string | null;
}

interface RepositoryActions {
  setRepositories: (repos: RepositoryInfo[]) => void;
  selectRepository: (repo: RepositoryInfo | null) => void;
  setAnalysisResult: (result: AnalysisResult | null) => void;
  setSemanticGraph: (graph: SemanticGraph | null) => void;
  addRepository: (repo: RepositoryInfo) => void;
  removeRepository: (id: string) => void;
  updateRepository: (id: string, updates: Partial<RepositoryInfo>) => void;
  setLoading: (loading: boolean) => void;
  setAnalyzing: (analyzing: boolean) => void;
  setImporting: (importing: boolean) => void;
  setError: (error: string | null) => void;
  clearError: () => void;
}

type RepositoryStore = RepositoryState & RepositoryActions;

export const useRepositoryStore = create<RepositoryStore>()((set) => ({
  repositories: [],
  selectedRepository: null,
  analysisResult: null,
  semanticGraph: null,
  isLoading: false,
  isAnalyzing: false,
  isImporting: false,
  error: null,

  setRepositories: (repositories) => set({ repositories }),

  selectRepository: (selectedRepository) => set({ selectedRepository }),

  setAnalysisResult: (analysisResult) => set({ analysisResult }),

  setSemanticGraph: (semanticGraph) => set({ semanticGraph }),

  addRepository: (repo) =>
    set((state) => ({ repositories: [...state.repositories, repo] })),

  removeRepository: (id) =>
    set((state) => ({
      repositories: state.repositories.filter((r) => r.id !== id),
      selectedRepository:
        state.selectedRepository?.id === id ? null : state.selectedRepository,
    })),

  updateRepository: (id, updates) =>
    set((state) => ({
      repositories: state.repositories.map((r) =>
        r.id === id ? { ...r, ...updates } : r
      ),
      selectedRepository:
        state.selectedRepository?.id === id
          ? { ...state.selectedRepository, ...updates }
          : state.selectedRepository,
    })),

  setLoading: (isLoading) => set({ isLoading }),

  setAnalyzing: (isAnalyzing) => set({ isAnalyzing }),

  setImporting: (isImporting) => set({ isImporting }),

  setError: (error) => set({ error }),

  clearError: () => set({ error: null }),
}));
