"use client";

import * as React from "react";
import { ListChecks, Sparkles, AlertTriangle, Target } from "lucide-react";
import { usePlannerStore } from "@/stores/planner-store";
import { plannerService } from "@/services/planner.service";
import { memoryService } from "@/services/memory.service";
import { PlanInput } from "./plan-input";
import { PlanDisplay } from "./plan-display";
import { PlanHistory } from "./plan-history";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ErrorState } from "@/components/ui/error-state";
import type { PlanRequest, ExecutionPlan, PlanHistoryItem } from "@/types/planner";
import type { IndexedRepository } from "@/types/memory";

export function PlannerWorkspace() {
  const {
    currentPlan,
    planHistory,
    isPlanning,
    isLoading,
    error,
    setCurrentPlan,
    setPlanHistory,
    setPlanning,
    setLoading,
    setError,
    clearError,
    removeFromHistory,
  } = usePlannerStore();

  const [repositories, setRepositories] = React.useState<IndexedRepository[]>(
    []
  );

  const loadInitialData = React.useCallback(async () => {
    setLoading(true);
    clearError();
    try {
      const [historyResult, reposResult] = await Promise.allSettled([
        plannerService.listPlans(),
        memoryService.listRepositories(),
      ]);

      if (historyResult.status === "fulfilled") {
        setPlanHistory(historyResult.value.data);
      } else {
        console.error("Failed to load plan history:", historyResult.reason);
      }

      if (reposResult.status === "fulfilled") {
        setRepositories(reposResult.value.data);
      } else {
        console.error("Failed to load repositories:", reposResult.reason);
      }

      if (historyResult.status === "rejected" && reposResult.status === "rejected") {
        setError("Failed to load planner data. Is the backend server running on port 8000?");
      }
    } catch (err: any) {
      setError(err.message || "Failed to load planner data");
    } finally {
      setLoading(false);
    }
  }, [setLoading, clearError, setPlanHistory, setError]);

  React.useEffect(() => {
    loadInitialData();
  }, [loadInitialData]);

  const handleCreatePlan = React.useCallback(
    async (request: PlanRequest) => {
      setPlanning(true);
      setError(null);
      try {
        const response = await plannerService.createPlan(request);
        setCurrentPlan(response.data);
        const historyItem: PlanHistoryItem = {
          id: response.data.id,
          objective: response.data.objective,
          intent: response.data.intent,
          complexity: response.data.complexity,
          task_count: response.data.tasks.length,
          risk_count: response.data.risks.length,
          estimated_duration_minutes: response.data.estimated_duration_minutes,
          created_at: response.data.created_at,
          repository_name: response.data.repository_name,
        };
        // Add to history if not already there
        const exists = planHistory.some((p) => p.id === historyItem.id);
        if (!exists) {
          setPlanHistory([historyItem, ...planHistory]);
        }
      } catch (err: any) {
        setError(
          err.response?.data?.detail || "Failed to generate plan"
        );
      } finally {
        setPlanning(false);
      }
    },
    [setPlanning, setError, setCurrentPlan, setPlanHistory, planHistory]
  );

  const handleSelectPlanFromHistory = React.useCallback(
    async (planItem: PlanHistoryItem) => {
      if (currentPlan?.id === planItem.id) return;
      setLoading(true);
      setError(null);
      try {
        const response = await plannerService.getPlan(planItem.id);
        setCurrentPlan(response.data);
      } catch (err: any) {
        setError(
          err.response?.data?.detail || "Failed to load plan"
        );
      } finally {
        setLoading(false);
      }
    },
    [currentPlan, setLoading, setError, setCurrentPlan]
  );

  const handleDeletePlan = React.useCallback(
    async (id: string) => {
      try {
        await plannerService.deletePlan(id);
        removeFromHistory(id);
        if (currentPlan?.id === id) {
          setCurrentPlan(null);
        }
      } catch (err: any) {
        setError(
          err.response?.data?.detail || "Failed to delete plan"
        );
      }
    },
    [currentPlan, removeFromHistory, setCurrentPlan, setError]
  );

  const handleApprove = React.useCallback(() => {
    // In a real app this would call an approval endpoint
    if (currentPlan) {
      setCurrentPlan({ ...currentPlan, approval_required: false });
    }
  }, [currentPlan, setCurrentPlan]);

  const handleRequestChanges = React.useCallback(
    (feedback: string) => {
      // In a real app this would submit feedback to the backend
      setCurrentPlan(null);
      setPlanning(false);
    },
    [setCurrentPlan, setPlanning]
  );

  const handleBack = React.useCallback(() => {
    setCurrentPlan(null);
  }, [setCurrentPlan]);

  const recentPlans = planHistory.slice(0, 5).map((p) => ({
    objective: p.objective,
    created_at: p.created_at,
  }));

  if (isLoading && !currentPlan) {
    return (
      <div className="flex flex-col h-full p-6 space-y-6">
        <div className="flex items-center space-x-3">
          <Skeleton variant="circular" className="h-8 w-8" />
          <Skeleton className="h-8 w-48" />
        </div>
        <div className="grid grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
        <Skeleton className="flex-1" />
      </div>
    );
  }

  return (
    <div className="flex h-full">
      <div className="flex-1 flex flex-col min-w-0">
        {currentPlan ? (
          <PlanDisplay
            plan={currentPlan}
            onBack={handleBack}
            onApprove={handleApprove}
            onRequestChanges={handleRequestChanges}
            isApproving={false}
          />
        ) : (
          <div className="flex flex-col h-full">
            <div className="flex items-center justify-between px-6 py-4 border-b border-border">
              <div className="flex items-center space-x-3">
                <div className="rounded-lg bg-accent/10 p-2">
                  <ListChecks className="h-5 w-5 text-accent" />
                </div>
                <div>
                  <h1 className="text-xl font-semibold text-text">
                    AI Planner
                  </h1>
                  <p className="text-sm text-text-muted">
                    Generate structured execution plans with risk analysis
                  </p>
                </div>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={loadInitialData}
                isLoading={isLoading}
              >
                Refresh
              </Button>
            </div>

            {error && (
              <div className="mx-6 mt-4">
                <ErrorState
                  title="Error"
                  description={error}
                  onRetry={clearError}
                />
              </div>
            )}

            <div className="flex-1 overflow-auto px-6 py-6">
              <div className="space-y-6">
                <div className="rounded-xl border border-border bg-surface p-6">
                  <div className="flex items-center space-x-2 mb-4">
                    <Sparkles className="h-5 w-5 text-accent" />
                    <h2 className="text-lg font-semibold text-text">
                      Create Execution Plan
                    </h2>
                  </div>
                  <PlanInput
                    onSubmit={handleCreatePlan}
                    isLoading={isPlanning}
                    recentPlans={recentPlans}
                    repositories={repositories}
                  />
                </div>

                {isPlanning && (
                  <div className="flex items-center gap-3 py-4">
                    <div className="relative">
                      <div className="h-8 w-8 rounded-full border-2 border-accent/20 border-t-accent animate-spin" />
                      <Sparkles className="h-4 w-4 text-accent absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-text">
                        Generating execution plan...
                      </p>
                      <p className="text-xs text-text-muted">
                        Analyzing objective and creating structured tasks
                      </p>
                    </div>
                  </div>
                )}

                {!isPlanning && planHistory.length === 0 && !error && (
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="rounded-xl border border-border bg-surface p-5">
                      <div className="flex items-center gap-3 mb-3">
                        <div className="p-2 rounded-lg bg-blue-500/10">
                          <ListChecks className="h-5 w-5 text-blue-400" />
                        </div>
                        <h3 className="font-medium text-text">Task Breakdown</h3>
                      </div>
                      <p className="text-sm text-text-muted">
                        Automatically decompose complex objectives into actionable tasks with clear dependencies.
                      </p>
                    </div>
                    <div className="rounded-xl border border-border bg-surface p-5">
                      <div className="flex items-center gap-3 mb-3">
                        <div className="p-2 rounded-lg bg-yellow-500/10">
                          <AlertTriangle className="h-5 w-5 text-yellow-400" />
                        </div>
                        <h3 className="font-medium text-text">Risk Analysis</h3>
                      </div>
                      <p className="text-sm text-text-muted">
                        Identify potential risks, edge cases, and blockers before implementation begins.
                      </p>
                    </div>
                    <div className="rounded-xl border border-border bg-surface p-5">
                      <div className="flex items-center gap-3 mb-3">
                        <div className="p-2 rounded-lg bg-green-500/10">
                          <Target className="h-5 w-5 text-green-400" />
                        </div>
                        <h3 className="font-medium text-text">Complexity Scoring</h3>
                      </div>
                      <p className="text-sm text-text-muted">
                        Get time estimates and complexity ratings to plan your sprints effectively.
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      <PlanHistory
        plans={planHistory}
        onSelectPlan={handleSelectPlanFromHistory}
        onDeletePlan={handleDeletePlan}
        selectedPlanId={currentPlan?.id || null}
        isLoading={isLoading}
      />
    </div>
  );
}
