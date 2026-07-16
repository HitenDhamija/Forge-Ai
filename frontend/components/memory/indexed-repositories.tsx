"use client";

import * as React from "react";
import {
  Database,
  RefreshCw,
  Trash2,
  AlertCircle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import type { IndexedRepository } from "@/types/memory";

interface IndexedRepositoriesProps {
  repositories: IndexedRepository[];
  onDelete: (id: string) => void;
  onReindex: (repo: IndexedRepository) => void;
}

export function IndexedRepositories({
  repositories,
  onDelete,
  onReindex,
}: IndexedRepositoriesProps) {
  const [deletingId, setDeletingId] = React.useState<string | null>(null);
  const [confirmDelete, setConfirmDelete] = React.useState<string | null>(null);

  const handleDelete = async (id: string) => {
    setDeletingId(id);
    try {
      await onDelete(id);
    } finally {
      setDeletingId(null);
      setConfirmDelete(null);
    }
  };

  if (repositories.length === 0) {
    return (
      <EmptyState
        icon={<Database className="h-12 w-12" />}
        title="No indexed repositories"
        description="Index a repository to start building semantic memory."
      />
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-text">
          Indexed Repositories
        </h3>
        <span className="text-xs text-text-muted">
          {repositories.length} repositories
        </span>
      </div>

      <div className="grid gap-3">
        {repositories.map((repo) => (
          <Card key={repo.id} className="hover:border-accent/50 transition-colors">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3 min-w-0">
                  <div className="rounded-lg bg-surface-hover p-2">
                    <Database className="h-4 w-4 text-accent" />
                  </div>
                  <div className="min-w-0">
                    <h4 className="text-sm font-medium text-text truncate">
                      {repo.name}
                    </h4>
                    <div className="flex items-center space-x-2 mt-1">
                      <Badge variant="secondary" className="text-xs">
                        {repo.chunks_count || 0} chunks
                      </Badge>
                      <span className="text-xs text-text-muted">
                        ID: {repo.id.substring(0, 8)}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center space-x-2 shrink-0">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onReindex(repo)}
                    title="Re-index repository"
                  >
                    <RefreshCw className="h-4 w-4" />
                  </Button>

                  {confirmDelete === repo.id ? (
                    <div className="flex items-center space-x-1">
                      <Button
                        variant="destructive"
                        size="sm"
                        onClick={() => handleDelete(repo.id)}
                        isLoading={deletingId === repo.id}
                      >
                        Confirm
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setConfirmDelete(null)}
                      >
                        Cancel
                      </Button>
                    </div>
                  ) : (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setConfirmDelete(repo.id)}
                      title="Delete from memory"
                      className="text-text-muted hover:text-danger"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
