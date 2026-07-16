"use client";

import { StudioLayout } from "@/components/studio/studio-layout";
import { WorkflowBuilder } from "@/components/studio/workflow-builder";
import { PromptStudio } from "@/components/studio/prompt-studio";
import { ExecutionReplay } from "@/components/studio/execution-replay";
import { AgentPlayground } from "@/components/studio/agent-playground";
import { MemoryExplorer } from "@/components/studio/memory-explorer";
import { ModelManager } from "@/components/studio/model-manager";
import { useStudioStore } from "@/stores/studio-store";

const sectionComponents = {
  workflows: WorkflowBuilder,
  prompts: PromptStudio,
  replay: ExecutionReplay,
  agents: AgentPlayground,
  workspace: WorkspaceOverviewPlaceholder,
  models: ModelManager,
  memory: MemoryExplorer,
};

function WorkspaceOverviewPlaceholder() {
  return (
    <div className="flex h-full items-center justify-center">
      <div className="text-center">
        <p className="text-text-muted">Workspace overview coming soon</p>
      </div>
    </div>
  );
}

export default function StudioPage() {
  const { activeSection } = useStudioStore();
  const ActiveComponent = sectionComponents[activeSection] || WorkflowBuilder;

  return (
    <StudioLayout>
      <ActiveComponent />
    </StudioLayout>
  );
}
