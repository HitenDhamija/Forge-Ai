"use client";

import * as React from "react";
import { GitBranch } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/ui/empty-state";
import { RepositoryCard } from "./repository-card";
import type { RepositoryInfo } from "@/types/repository";

interface RepositoryListProps {
  repositories: RepositoryInfo[];
  isLoading?: boolean;
  searchQuery?: string;
  onDelete?: (id: string) => void;
}

function RepositoryList({
  repositories,
  isLoading = false,
  searchQuery = "",
  onDelete,
}: RepositoryListProps) {
  const repoList = Array.isArray(repositories) ? repositories : [];

  if (isLoading) {
    return (
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <div
            key={i}
            className="rounded-lg border border-border bg-surface p-6"
          >
            <div className="mb-4 flex items-center space-x-3">
              <Skeleton className="h-10 w-10 rounded-md" />
              <div className="space-y-2">
                <Skeleton className="h-5 w-32" />
                <Skeleton className="h-4 w-48" />
              </div>
            </div>
            <div className="space-y-3">
              <div className="flex gap-2">
                <Skeleton className="h-5 w-16 rounded-full" />
                <Skeleton className="h-5 w-12 rounded-full" />
              </div>
              <div className="flex gap-1">
                <Skeleton className="h-4 w-14 rounded-full" />
                <Skeleton className="h-4 w-16 rounded-full" />
              </div>
              <Skeleton className="h-3 w-24" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (repoList.length === 0) {
    return (
      <EmptyState
        icon={<GitBranch className="h-12 w-12" />}
        title="No repositories found"
        description={
          searchQuery
            ? "No repositories match your search criteria."
            : "Import your first repository to get started with code analysis."
        }
      />
    );
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {repoList.map((repo, index) => (
        <RepositoryCard
          key={repo.id || `repo-${index}`}
          repository={repo}
          onDelete={onDelete}
        />
      ))}
    </div>
  );
}

export { RepositoryList };
