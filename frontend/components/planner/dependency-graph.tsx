"use client";

import * as React from "react";
import {
  Package,
  FileCode,
  Database,
  Globe,
  Check,
  X,
  ExternalLink,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { DependencyInfo, Task } from "@/types/planner";

interface DependencyGraphProps {
  dependencies: DependencyInfo[];
  tasks: Task[];
  highlightedDep: string | null;
  onHighlightDep: (name: string | null) => void;
}

const DEP_TYPE_CONFIG: Record<
  string,
  { icon: React.ReactNode; color: string; bgColor: string }
> = {
  package: {
    icon: <Package className="h-4 w-4" />,
    color: "text-accent",
    bgColor: "bg-accent/10",
  },
  module: {
    icon: <FileCode className="h-4 w-4" />,
    color: "text-warning",
    bgColor: "bg-warning/10",
  },
  database: {
    icon: <Database className="h-4 w-4" />,
    color: "text-success",
    bgColor: "bg-success/10",
  },
  service: {
    icon: <Globe className="h-4 w-4" />,
    color: "text-danger",
    bgColor: "bg-danger/10",
  },
};

export function DependencyGraph({
  dependencies,
  tasks,
  highlightedDep,
  onHighlightDep,
}: DependencyGraphProps) {
  if (dependencies.length === 0) {
    return (
      <div className="flex items-center justify-center py-12 text-text-muted">
        <p className="text-sm">No dependencies found</p>
      </div>
    );
  }

  const groupedByType = dependencies.reduce<
    Record<string, DependencyInfo[]>
  >((acc, dep) => {
    if (!acc[dep.type]) acc[dep.type] = [];
    acc[dep.type].push(dep);
    return acc;
  }, {});

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-text-muted uppercase tracking-wide">
          {dependencies.length} Dependencies
        </span>
        <div className="flex items-center space-x-2">
          {Object.entries(groupedByType).map(([type, deps]) => {
            const config = DEP_TYPE_CONFIG[type] || DEP_TYPE_CONFIG.package;
            return (
              <div
                key={type}
                className="flex items-center space-x-1 text-xs text-text-muted"
              >
                <span className={config.color}>{config.icon}</span>
                <span>{deps.length}</span>
              </div>
            );
          })}
        </div>
      </div>

      <div className="space-y-3">
        {Object.entries(groupedByType).map(([type, deps]) => {
          const config = DEP_TYPE_CONFIG[type] || DEP_TYPE_CONFIG.package;
          return (
            <div key={type} className="space-y-2">
              <h4
                className={cn(
                  "text-xs font-medium uppercase tracking-wide flex items-center",
                  config.color
                )}
              >
                {config.icon}
                <span className="ml-2">{type}</span>
              </h4>
              <div className="grid grid-cols-2 gap-2">
                {deps.map((dep) => {
                  const isHighlighted = highlightedDep === dep.name;
                  const tasksUsingDep = tasks.filter((t) =>
                    dep.required_by?.includes(t.id)
                  );
                  return (
                    <div
                      key={dep.name}
                      className={cn(
                        "rounded-lg border p-3 transition-all cursor-pointer",
                        isHighlighted
                          ? "border-accent bg-accent/5"
                          : "border-border bg-surface hover:bg-surface-hover",
                        dep.exists
                          ? "border-l-2 border-l-success"
                          : "border-l-2 border-l-danger"
                      )}
                      onClick={() =>
                        onHighlightDep(isHighlighted ? null : dep.name)
                      }
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-2 min-w-0">
                          <span className={config.color}>{config.icon}</span>
                          <span className="text-sm font-medium text-text truncate">
                            {dep.name}
                          </span>
                        </div>
                        <div className="flex items-center space-x-1 shrink-0">
                          {dep.exists ? (
                            <Check className="h-4 w-4 text-success" />
                          ) : (
                            <X className="h-4 w-4 text-danger" />
                          )}
                          {dep.path && (
                            <ExternalLink className="h-3 w-3 text-text-muted" />
                          )}
                        </div>
                      </div>

                      {dep.path && (
                        <p className="mt-1 text-xs text-text-muted font-mono truncate">
                          {dep.path}
                        </p>
                      )}

                      {tasksUsingDep.length > 0 && (
                        <div className="mt-2 flex flex-wrap gap-1">
                          {tasksUsingDep.map((t) => (
                            <Badge
                              key={t.id}
                              variant="secondary"
                              className="text-xs"
                            >
                              {t.id}
                            </Badge>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>

      <div className="rounded-lg border border-border bg-surface p-3">
        <h4 className="text-xs font-medium text-text-muted uppercase tracking-wide mb-2">
          Legend
        </h4>
        <div className="flex flex-wrap gap-3">
          <div className="flex items-center space-x-1 text-xs text-text-muted">
            <span className="h-3 w-3 rounded-full bg-success" />
            <span>Exists</span>
          </div>
          <div className="flex items-center space-x-1 text-xs text-text-muted">
            <span className="h-3 w-3 rounded-full bg-danger" />
            <span>Missing</span>
          </div>
          <div className="flex items-center space-x-1 text-xs text-text-muted">
            <span className="h-3 w-3 rounded-full bg-accent" />
            <span>Highlighted</span>
          </div>
        </div>
      </div>
    </div>
  );
}
