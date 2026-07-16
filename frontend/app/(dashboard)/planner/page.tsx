"use client";

import { PlannerWorkspace } from "@/components/planner/planner-workspace";

export default function PlannerPage() {
  return (
    <div className="flex h-[calc(100vh-4rem)] -m-6">
      <PlannerWorkspace />
    </div>
  );
}
