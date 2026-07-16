"use client";

import * as React from "react";
import {
  Sparkles,
  Clock,
  GitBranch,
  Plus,
  X,
  FileText,
  Lightbulb,
  Code,
  Shield,
  Rocket,
  TestTube,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import type { PlanRequest } from "@/types/planner";
import type { IndexedRepository } from "@/types/memory";

interface PlanInputProps {
  onSubmit: (request: PlanRequest) => void;
  isLoading: boolean;
  recentPlans: { objective: string; created_at: string }[];
  repositories: IndexedRepository[];
}

const EXAMPLE_PROMPTS = [
  {
    icon: Code,
    label: "Add Authentication",
    prompt: "Add user authentication with JWT tokens, including login, signup, and password reset",
    color: "text-blue-400",
  },
  {
    icon: Shield,
    label: "Security Audit",
    prompt: "Perform a security audit and fix all vulnerabilities including XSS, SQL injection, and hardcoded secrets",
    color: "text-red-400",
  },
  {
    icon: TestTube,
    label: "Add Tests",
    prompt: "Add comprehensive unit tests and integration tests for all main features",
    color: "text-green-400",
  },
  {
    icon: Rocket,
    label: "Deploy Setup",
    prompt: "Set up Docker containerization and CI/CD pipeline with GitHub Actions",
    color: "text-purple-400",
  },
];

export function PlanInput({
  onSubmit,
  isLoading,
  recentPlans,
  repositories,
}: PlanInputProps) {
  const [objective, setObjective] = React.useState("");
  const [repositoryId, setRepositoryId] = React.useState("");
  const [additionalContext, setAdditionalContext] = React.useState("");
  const [constraint, setConstraint] = React.useState("");
  const [constraints, setConstraints] = React.useState<string[]>([]);
  const [showAdvanced, setShowAdvanced] = React.useState(false);
  const textareaRef = React.useRef<HTMLTextAreaElement>(null);

  React.useEffect(() => {
    textareaRef.current?.focus();
  }, []);

  const handleAddConstraint = () => {
    const trimmed = constraint.trim();
    if (trimmed && !constraints.includes(trimmed)) {
      setConstraints((prev) => [...prev, trimmed]);
      setConstraint("");
    }
  };

  const handleRemoveConstraint = (c: string) => {
    setConstraints((prev) => prev.filter((item) => item !== c));
  };

  const handleConstraintKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleAddConstraint();
    }
  };

  const handleSubmit = () => {
    if (!objective.trim() || isLoading) return;
    const request: PlanRequest = {
      objective: objective.trim(),
      additional_context: additionalContext.trim() || undefined,
      constraints: constraints.length > 0 ? constraints : undefined,
    };
    if (repositoryId) {
      const repo = repositories.find((r) => r.id === repositoryId);
      request.repository_id = repositoryId;
      request.repository_name = repo?.name;
    }
    onSubmit(request);
  };

  const handleObjectiveKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleExampleClick = (prompt: string) => {
    setObjective(prompt);
    textareaRef.current?.focus();
  };

  return (
    <div className="space-y-5">
      {/* Project Selector - Always visible */}
      <div className="flex items-center gap-3">
        <GitBranch className="h-4 w-4 text-text-muted" />
        <select
          value={repositoryId}
          onChange={(e) => setRepositoryId(e.target.value)}
          className="flex-1 h-10 rounded-lg border border-border bg-bg px-3 text-sm text-text focus:border-accent focus:outline-none"
          disabled={isLoading}
        >
          <option value="">
            {repositories.length === 0
              ? "No projects found - import a repository first"
              : "Select a project (optional)"}
          </option>
          {repositories.map((repo) => (
            <option key={repo.id} value={repo.id}>
              {repo.name}
            </option>
          ))}
        </select>
        {repositoryId && (
          <span className="text-xs text-accent">
            {repositories.find(r => r.id === repositoryId)?.name}
          </span>
        )}
      </div>

      <div className="space-y-3">
        <div className="relative">
          <Textarea
            ref={textareaRef}
            value={objective}
            onChange={(e) => setObjective(e.target.value)}
            onKeyDown={handleObjectiveKeyDown}
            placeholder={repositoryId ? "Describe what you want to do with this project..." : "Describe what you want to build, fix, or accomplish..."}
            className="min-h-[140px] text-base resize-none pr-4"
            disabled={isLoading}
          />
          <div className="absolute bottom-3 right-3 text-xs text-text-muted">
            {objective.length > 0 && (
              <span>{objective.length} chars</span>
            )}
          </div>
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowAdvanced(!showAdvanced)}
            >
              {showAdvanced ? "Hide" : "Show"} Options
            </Button>
            {repositories.length > 0 && (
              <span className="text-xs text-text-muted">
                {repositories.length} repos available
              </span>
            )}
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-xs text-text-muted">
              {isLoading ? "Generating..." : "Ctrl+Enter to generate"}
            </span>
            <Button
              onClick={handleSubmit}
              disabled={!objective.trim() || isLoading}
              isLoading={isLoading}
              leftIcon={<Sparkles className="h-4 w-4" />}
            >
              Generate Plan
            </Button>
          </div>
        </div>
      </div>

      {/* Example Prompts */}
      {!objective && (
        <div className="space-y-3">
          <div className="flex items-center gap-2 text-sm text-text-muted">
            <Lightbulb className="h-4 w-4 text-warning" />
            <span>Try one of these examples</span>
          </div>
          <div className="grid grid-cols-2 gap-2">
            {EXAMPLE_PROMPTS.map((example) => (
              <button
                key={example.label}
                onClick={() => handleExampleClick(example.prompt)}
                className="flex items-center gap-3 p-3 rounded-lg border border-border bg-surface hover:bg-surface-hover hover:border-accent/30 transition-all text-left group"
              >
                <div className={`p-2 rounded-md bg-bg ${example.color} group-hover:scale-110 transition-transform`}>
                  <example.icon className="h-4 w-4" />
                </div>
                <span className="text-sm font-medium text-text">{example.label}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {showAdvanced && (
        <div className="rounded-lg border border-border bg-surface p-4 space-y-4">
          <h4 className="text-sm font-medium text-text">Advanced Options</h4>

          {repositories.length > 0 && (
            <div className="space-y-2">
              <label className="text-xs font-medium text-text-muted uppercase tracking-wide flex items-center">
                <GitBranch className="h-3 w-3 mr-1" />
                Repository (optional)
              </label>
              <select
                value={repositoryId}
                onChange={(e) => setRepositoryId(e.target.value)}
                className="w-full h-9 rounded-md border border-border bg-bg px-3 text-sm text-text focus:border-accent focus:outline-none"
                disabled={isLoading}
              >
                <option value="">No repository selected</option>
                {repositories.map((repo) => (
                  <option key={repo.id} value={repo.id}>
                    {repo.name}
                  </option>
                ))}
              </select>
            </div>
          )}

          <div className="space-y-2">
            <label className="text-xs font-medium text-text-muted uppercase tracking-wide flex items-center">
              <FileText className="h-3 w-3 mr-1" />
              Additional Context (optional)
            </label>
            <Textarea
              value={additionalContext}
              onChange={(e) => setAdditionalContext(e.target.value)}
              placeholder="Any extra context the planner should know about..."
              className="min-h-[80px] text-sm resize-none"
              disabled={isLoading}
            />
          </div>

          <div className="space-y-2">
            <label className="text-xs font-medium text-text-muted uppercase tracking-wide flex items-center">
              <Clock className="h-3 w-3 mr-1" />
              Constraints (optional)
            </label>
            <div className="flex items-center space-x-2">
              <Input
                value={constraint}
                onChange={(e) => setConstraint(e.target.value)}
                onKeyDown={handleConstraintKeyDown}
                placeholder="e.g. Must not break existing API"
                className="flex-1 h-9"
                disabled={isLoading}
              />
              <Button
                variant="outline"
                size="sm"
                onClick={handleAddConstraint}
                disabled={!constraint.trim() || isLoading}
                leftIcon={<Plus className="h-4 w-4" />}
              >
                Add
              </Button>
            </div>
            {constraints.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-2">
                {constraints.map((c) => (
                  <Badge
                    key={c}
                    variant="secondary"
                    className="flex items-center gap-1"
                  >
                    {c}
                    <button
                      onClick={() => handleRemoveConstraint(c)}
                      className="ml-1 hover:text-danger"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </Badge>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {recentPlans.length > 0 && !objective && (
        <div className="space-y-2">
          <h4 className="text-xs font-medium text-text-muted uppercase tracking-wide">
            Recent Plans
          </h4>
          <div className="space-y-1">
            {recentPlans.slice(0, 3).map((plan, i) => (
              <button
                key={`${plan.created_at}-${i}`}
                onClick={() => handleExampleClick(plan.objective)}
                className="w-full text-left px-3 py-2 rounded-md text-sm text-text-muted hover:text-text hover:bg-surface-hover transition-colors truncate"
              >
                {plan.objective}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
