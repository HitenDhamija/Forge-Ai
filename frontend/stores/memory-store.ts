import { create } from "zustand";
import type {
  SearchResult,
  ContextResponse,
  IndexedRepository,
  MemoryStats,
  CollectionStats,
} from "@/types/memory";

interface MemoryState {
  searchResults: SearchResult[];
  contextResponse: ContextResponse | null;
  indexedRepositories: IndexedRepository[];
  memoryStats: MemoryStats | null;
  collections: CollectionStats[];
  isSearching: boolean;
  isIndexing: boolean;
  isLoading: boolean;
  error: string | null;
  lastQuery: string;
  searchHistory: string[];
}

interface MemoryActions {
  setSearchResults: (results: SearchResult[]) => void;
  setContextResponse: (context: ContextResponse | null) => void;
  setIndexedRepositories: (repos: IndexedRepository[]) => void;
  setMemoryStats: (stats: MemoryStats | null) => void;
  setCollections: (collections: CollectionStats[]) => void;
  setSearching: (searching: boolean) => void;
  setIndexing: (indexing: boolean) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearError: () => void;
  setLastQuery: (query: string) => void;
  addToHistory: (query: string) => void;
  clearResults: () => void;
}

type MemoryStore = MemoryState & MemoryActions;

export const useMemoryStore = create<MemoryStore>()((set) => ({
  searchResults: [],
  contextResponse: null,
  indexedRepositories: [],
  memoryStats: null,
  collections: [],
  isSearching: false,
  isIndexing: false,
  isLoading: false,
  error: null,
  lastQuery: "",
  searchHistory: [],

  setSearchResults: (searchResults) => set({ searchResults }),

  setContextResponse: (contextResponse) => set({ contextResponse }),

  setIndexedRepositories: (indexedRepositories) =>
    set({ indexedRepositories }),

  setMemoryStats: (memoryStats) => set({ memoryStats }),

  setCollections: (collections) => set({ collections }),

  setSearching: (isSearching) => set({ isSearching }),

  setIndexing: (isIndexing) => set({ isIndexing }),

  setLoading: (isLoading) => set({ isLoading }),

  setError: (error) => set({ error }),

  clearError: () => set({ error: null }),

  setLastQuery: (lastQuery) => set({ lastQuery }),

  addToHistory: (query) =>
    set((state) => ({
      searchHistory: [
        query,
        ...state.searchHistory.filter((q) => q !== query),
      ].slice(0, 10),
    })),

  clearResults: () =>
    set({
      searchResults: [],
      contextResponse: null,
    }),
}));
