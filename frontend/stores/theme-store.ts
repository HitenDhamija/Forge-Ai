import { create } from "zustand";
import { persist } from "zustand/middleware";

type Theme = "dark" | "light" | "system";

interface ThemeState {
  theme: Theme;
  isDark: boolean;
}

interface ThemeActions {
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
}

type ThemeStore = ThemeState & ThemeActions;

export const useThemeStore = create<ThemeStore>()(
  persist(
    (set, get) => ({
      theme: "dark",
      isDark: true,

      setTheme: (theme) => {
        const isDark =
          theme === "dark" ||
          (theme === "system" &&
            window.matchMedia("(prefers-color-scheme: dark)").matches);
        set({ theme, isDark });
      },

      toggleTheme: () => {
        const current = get().theme;
        const newTheme = current === "dark" ? "light" : "dark";
        set({ theme: newTheme, isDark: newTheme === "dark" });
      },
    }),
    {
      name: "forge-theme",
    }
  )
);
