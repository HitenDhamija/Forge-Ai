import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { Project } from "@/types/api";

interface ProjectState {
  projects: Project[];
  selectedProject: Project | null;
  isLoading: boolean;
}

interface ProjectActions {
  setProjects: (projects: Project[]) => void;
  selectProject: (project: Project | null) => void;
  addProject: (project: Project) => void;
  updateProject: (id: string, data: Partial<Project>) => void;
  removeProject: (id: string) => void;
  setLoading: (isLoading: boolean) => void;
}

type ProjectStore = ProjectState & ProjectActions;

export const useProjectStore = create<ProjectStore>()(
  persist(
    (set) => ({
      projects: [],
      selectedProject: null,
      isLoading: false,

      setProjects: (projects) => {
        const seen = new Set<string>();
        const deduped = projects.filter((p) => {
          if (seen.has(p.id)) return false;
          seen.add(p.id);
          return true;
        });
        set({ projects: deduped });
      },

      selectProject: (project) => set({ selectedProject: project }),

      addProject: (project) =>
        set((state) => {
          if (state.projects.some((p) => p.id === project.id)) return state;
          return { projects: [...state.projects, project] };
        }),

      updateProject: (id, data) =>
        set((state) => ({
          projects: state.projects.map((p) =>
            p.id === id ? { ...p, ...data } : p
          ),
          selectedProject:
            state.selectedProject?.id === id
              ? { ...state.selectedProject, ...data }
              : state.selectedProject,
        })),

      removeProject: (id) =>
        set((state) => ({
          projects: state.projects.filter((p) => p.id !== id),
          selectedProject:
            state.selectedProject?.id === id ? null : state.selectedProject,
        })),

      setLoading: (isLoading) => set({ isLoading }),
    }),
    {
      name: "forge-projects",
    }
  )
);
