import { apiClient } from "./api";
import type {
  RepositoryCreate,
  RepositoryInfo,
  AnalysisResult,
  SemanticGraph,
} from "@/types/repository";

const REPO_BASE = "/repositories";

export const repositoryService = {
  import: async (request: RepositoryCreate) => {
    const { data } = await apiClient.post<any>(`${REPO_BASE}/import`, request);
    return { data: data.data || data };
  },

  upload: async (formData: FormData) => {
    const { data } = await apiClient.post<any>(`${REPO_BASE}/import/upload`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return { data: data.data || data };
  },

  uploadFolder: async (formData: FormData) => {
    const { data } = await apiClient.post<any>(`${REPO_BASE}/import/folder`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
      timeout: 300000, // 5 minutes for large folder uploads
    });
    return { data: data.data || data };
  },

  importLocalFolder: async (formData: FormData) => {
    const { data } = await apiClient.post<any>(`${REPO_BASE}/import/local-folder`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return { data: data.data || data };
  },

  folderInit: async (formData: FormData) => {
    const { data } = await apiClient.post<any>(`${REPO_BASE}/import/folder/init`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return { data: data.data || data };
  },

  folderBatch: async (repoId: string, formData: FormData) => {
    const { data } = await apiClient.post<any>(`${REPO_BASE}/import/folder/${repoId}/batch`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
      timeout: 120000,
    });
    return { data: data.data || data };
  },

  folderFinalize: async (repoId: string) => {
    const { data } = await apiClient.post<any>(`${REPO_BASE}/import/folder/${repoId}/finalize`);
    return { data: data.data || data };
  },

  list: async () => {
    const { data } = await apiClient.get<any>(REPO_BASE);
    return { data: data.data || data };
  },

  get: async (id: string) => {
    const { data } = await apiClient.get<any>(`${REPO_BASE}/${id}`);
    // apiClient interceptor unwraps { status, data } so data is the repo object
    return { data: data };
  },

  delete: async (id: string) => {
    const { data } = await apiClient.delete<any>(`${REPO_BASE}/${id}`);
    return { data: data.data || data };
  },

  analyze: async (id: string) => {
    const { data } = await apiClient.post<any>(`${REPO_BASE}/${id}/analyze`);
    return { data: data };
  },

  getSummary: async (id: string) => {
    const { data } = await apiClient.get<any>(`${REPO_BASE}/${id}/summary`);
    return { data: data.data || data };
  },

  getAnalysis: async (id: string) => {
    const { data } = await apiClient.get<any>(`${REPO_BASE}/${id}/analysis`);
    return { data: data.data || data };
  },

  getGraph: async (id: string) => {
    const { data } = await apiClient.get<any>(`${REPO_BASE}/${id}/graph`);
    return { data: data.data || data };
  },
};
