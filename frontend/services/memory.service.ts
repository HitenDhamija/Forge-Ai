import { apiClient } from "./api";
import type {
  SearchRequest,
  SearchResponse,
  ContextRequest,
  ContextResponse,
  IndexRequest,
  IndexResponse,
  MemoryStats,
  IndexedRepository,
} from "@/types/memory";

const MEMORY_BASE = "/memory";

export const memoryService = {
  index: (request: IndexRequest) =>
    apiClient.post<IndexResponse>(`${MEMORY_BASE}/index`, request),

  search: (request: SearchRequest) =>
    apiClient.post<SearchResponse>(`${MEMORY_BASE}/search`, request),

  getContext: (request: ContextRequest) =>
    apiClient.post<ContextResponse>(`${MEMORY_BASE}/context`, request),

  listRepositories: () =>
    apiClient.get<IndexedRepository[]>(`${MEMORY_BASE}/repositories`),

  getStats: () => apiClient.get<MemoryStats>(`${MEMORY_BASE}/stats`),

  deleteRepository: (id: string) =>
    apiClient.delete(`${MEMORY_BASE}/index/${id}`),
};
