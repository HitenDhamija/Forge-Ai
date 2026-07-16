import { apiClient } from "./api";
import { API_ENDPOINTS } from "@/config/constants";
import type { ApiResponse, User, AuthCredentials, RegisterData, LoginResponse } from "@/types/api";

export const authService = {
  login: async (credentials: AuthCredentials) => {
    const response = await apiClient.post<ApiResponse<LoginResponse>>(
      API_ENDPOINTS.AUTH.LOGIN,
      credentials
    );
    return response.data as any;
  },

  register: async (data: RegisterData) => {
    const response = await apiClient.post<ApiResponse<LoginResponse>>(
      API_ENDPOINTS.AUTH.REGISTER,
      data
    );
    return response.data as any;
  },

  refreshToken: async (token: string) => {
    const response = await apiClient.post<ApiResponse<LoginResponse>>(
      API_ENDPOINTS.AUTH.REFRESH,
      { refreshToken: token }
    );
    return response.data as any;
  },

  logout: async () => {
    await apiClient.post(API_ENDPOINTS.AUTH.LOGOUT);
  },

  getProfile: async () => {
    const response = await apiClient.get<ApiResponse<User>>(
      API_ENDPOINTS.USERS.ME
    );
    return response.data as any;
  },
};
