"use client";

import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/auth-store";
import { authService } from "@/services/auth.service";
import { STORAGE_KEYS, ROUTES } from "@/config/constants";
import type { AuthCredentials, RegisterData } from "@/types/api";

export function useAuth() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading, login, logout, setLoading } =
    useAuthStore();

  const handleLogin = async (credentials: AuthCredentials) => {
    try {
      setLoading(true);
      const data = await authService.login(credentials);

      // authService returns the unwrapped { user, accessToken, refreshToken }
      const accessToken = data.accessToken;
      const refreshToken = data.refreshToken;
      const user = data.user;

      localStorage.setItem(STORAGE_KEYS.AUTH_TOKEN, accessToken);
      localStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, refreshToken);

      login(user, accessToken, refreshToken);
      router.push(ROUTES.DASHBOARD);
    } catch (error) {
      setLoading(false);
      throw error;
    }
  };

  const handleRegister = async (data: RegisterData) => {
    try {
      setLoading(true);
      const result = await authService.register(data);

      const accessToken = result.accessToken;
      const refreshToken = result.refreshToken;
      const user = result.user;

      localStorage.setItem(STORAGE_KEYS.AUTH_TOKEN, accessToken);
      localStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, refreshToken);

      login(user, accessToken, refreshToken);
      router.push(ROUTES.DASHBOARD);
    } catch (error) {
      setLoading(false);
      throw error;
    }
  };

  const handleLogout = async () => {
    try {
      await authService.logout();
    } finally {
      localStorage.removeItem(STORAGE_KEYS.AUTH_TOKEN);
      localStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN);
      logout();
      router.push(ROUTES.LOGIN);
    }
  };

  return {
    user,
    isAuthenticated,
    isLoading,
    login: handleLogin,
    register: handleRegister,
    logout: handleLogout,
  };
}
