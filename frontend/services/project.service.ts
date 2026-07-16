import { apiClient } from "./api";
import { API_ENDPOINTS } from "@/config/constants";
import type { ApiResponse, PaginatedResponse, Project } from "@/types/api";

interface ProjectParams {
  page?: number;
  pageSize?: number;
  search?: string;
  status?: string;
}

export const projectService = {
  getAll: async (params?: ProjectParams) => {
    const response = await apiClient.get<ApiResponse<PaginatedResponse<Project>>>(
      API_ENDPOINTS.PROJECTS.LIST,
      { params }
    );
    return response.data as any;
  },

  getById: async (id: string) => {
    const response = await apiClient.get<ApiResponse<Project>>(
      API_ENDPOINTS.PROJECTS.GET(id)
    );
    return response.data as any;
  },

  create: async (data: Partial<Project>) => {
    const response = await apiClient.post<ApiResponse<Project>>(
      API_ENDPOINTS.PROJECTS.CREATE,
      data
    );
    return response.data as any;
  },

  update: async (id: string, data: Partial<Project>) => {
    const response = await apiClient.put<ApiResponse<Project>>(
      API_ENDPOINTS.PROJECTS.UPDATE(id),
      data
    );
    return response.data as any;
  },

  delete: async (id: string) => {
    await apiClient.delete(API_ENDPOINTS.PROJECTS.DELETE(id));
  },
};
