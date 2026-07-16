"use client";

import * as React from "react";
import { Package } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { useDebounce } from "@/hooks/use-debounce";
import { cn } from "@/lib/utils";
import type { DependencyInfo } from "@/types/repository";

interface DependencyViewerProps {
  dependencies: DependencyInfo[];
}

function DependencyViewer({ dependencies }: DependencyViewerProps) {
  const [search, setSearch] = React.useState("");
  const [filter, setFilter] = React.useState<"all" | "production" | "development">("all");
  const debouncedSearch = useDebounce(search);

  const productionDeps = dependencies.filter((d) => d.is_production);
  const devDeps = dependencies.filter((d) => !d.is_production);

  const filtered = React.useMemo(() => {
    return dependencies.filter((dep) => {
      const matchesSearch =
        dep.name.toLowerCase().includes(debouncedSearch.toLowerCase()) ||
        dep.source_file.toLowerCase().includes(debouncedSearch.toLowerCase());
      const matchesFilter =
        filter === "all" ||
        (filter === "production" && dep.is_production) ||
        (filter === "development" && !dep.is_production);
      return matchesSearch && matchesFilter;
    });
  }, [dependencies, debouncedSearch, filter]);

  if (dependencies.length === 0) {
    return (
      <p className="text-sm text-text-muted">No dependencies detected</p>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center space-x-2">
          <Badge variant="default">
            {productionDeps.length} production
          </Badge>
          <Badge variant="secondary">
            {devDeps.length} development
          </Badge>
        </div>
        <div className="flex items-center space-x-2">
          <div className="flex rounded-md border border-border bg-surface">
            {(["all", "production", "development"] as const).map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={cn(
                  "px-3 py-1.5 text-xs font-medium capitalize transition-colors",
                  filter === f
                    ? "bg-surface-active text-text"
                    : "text-text-muted hover:text-text"
                )}
              >
                {f}
              </button>
            ))}
          </div>
          <Input
            placeholder="Search dependencies..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-48"
          />
        </div>
      </div>

      <div className="space-y-1">
        {filtered.map((dep) => (
          <div
            key={dep.name}
            className="flex items-center justify-between rounded-md border border-border px-3 py-2 transition-colors hover:bg-surface-hover"
          >
            <div className="flex items-center space-x-3">
              <Package className="h-4 w-4 text-text-muted" />
              <div>
                <span className="text-sm font-medium text-text">
                  {dep.name}
                </span>
                {dep.version && (
                  <span className="ml-2 text-xs text-text-muted">
                    v{dep.version}
                  </span>
                )}
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <Badge
                variant={dep.is_production ? "default" : "secondary"}
                className="text-xs"
              >
                {dep.is_production ? "prod" : "dev"}
              </Badge>
              <span className="font-mono text-xs text-text-muted">
                {dep.source_file}
              </span>
            </div>
          </div>
        ))}
      </div>

      {filtered.length === 0 && (
        <p className="text-center text-sm text-text-muted">
          No dependencies match your search
        </p>
      )}
    </div>
  );
}

export { DependencyViewer };
