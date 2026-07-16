import { create } from "zustand";
import type { ExecutionPlan, PlanHistoryItem, Task } from "@/types/planner";

interface PlannerState {
  currentPlan: ExecutionPlan | null;
  planHistory: PlanHistoryItem[];
  isPlanning: boolean;
  isLoading: boolean;
  error: string | null;
  selectedTask: Task | null;
}

interface PlannerActions {
  setCurrentPlan: (plan: ExecutionPlan | null) => void;
  setPlanHistory: (history: PlanHistoryItem[]) => void;
  setPlanning: (planning: boolean) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearError: () => void;
  setSelectedTask: (task: Task | null) => void;
  addToHistory: (item: PlanHistoryItem) => void;
  removeFromHistory: (id: string) => void;
}

type PlannerStore = PlannerState & PlannerActions;

export const usePlannerStore = create<PlannerStore>()((set) => ({
  currentPlan: null,
  planHistory: [],
  isPlanning: false,
  isLoading: false,
  error: null,
  selectedTask: null,

  setCurrentPlan: (currentPlan) => set({ currentPlan }),

  setPlanHistory: (planHistory) => set({ planHistory }),

  setPlanning: (isPlanning) => set({ isPlanning }),

  setLoading: (isLoading) => set({ isLoading }),

  setError: (error) => set({ error }),

  clearError: () => set({ error: null }),

  setSelectedTask: (selectedTask) => set({ selectedTask }),

  addToHistory: (item) =>
    set((state) => ({
      planHistory: [item, ...state.planHistory],
    })),

  removeFromHistory: (id) =>
    set((state) => ({
      planHistory: state.planHistory.filter((item) => item.id !== id),
    })),
}));
