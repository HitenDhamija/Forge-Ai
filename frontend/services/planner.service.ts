import { apiClient } from "./api";
import type { PlanRequest, ExecutionPlan, PlanHistoryItem } from "@/types/planner";

const PLANNER_BASE = "/planner";

export const plannerService = {
  createPlan: (request: PlanRequest) =>
    apiClient.post<ExecutionPlan>(`${PLANNER_BASE}/plan`, request),

  listPlans: () =>
    apiClient.get<PlanHistoryItem[]>(`${PLANNER_BASE}/history`),

  getPlan: (id: string) =>
    apiClient.get<ExecutionPlan>(`${PLANNER_BASE}/${id}`),

  deletePlan: (id: string) =>
    apiClient.delete(`${PLANNER_BASE}/${id}`),
};
