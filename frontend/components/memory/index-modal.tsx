"use client";

import * as React from "react";
import {
  Zap,
  RefreshCw,
  Check,
  AlertCircle,
} from "lucide-react";
import {
  Modal,
  ModalContent,
  ModalHeader,
  ModalTitle,
  ModalDescription,
  ModalFooter,
} from "@/components/ui/modal";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import type { IndexedRepository } from "@/types/memory";

interface IndexModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onIndex: (
    repositoryId: string,
    repositoryName: string,
    forceReindex: boolean
  ) => Promise<void>;
  isIndexing: boolean;
  repositories: IndexedRepository[];
}

export function IndexModal({
  open,
  onOpenChange,
  onIndex,
  isIndexing,
  repositories,
}: IndexModalProps) {
  const [selectedRepo, setSelectedRepo] =
    React.useState<IndexedRepository | null>(null);
  const [forceReindex, setForceReindex] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [success, setSuccess] = React.useState(false);

  const handleOpenChange = (open: boolean) => {
    if (!open) {
      setSelectedRepo(null);
      setForceReindex(false);
      setError(null);
      setSuccess(false);
    }
    onOpenChange(open);
  };

  const handleIndex = async () => {
    if (!selectedRepo) return;
    setError(null);
    setSuccess(false);
    try {
      await onIndex(selectedRepo.id, selectedRepo.name, forceReindex);
      setSuccess(true);
      setTimeout(() => handleOpenChange(false), 1500);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Indexing failed");
    }
  };

  return (
    <Modal open={open} onOpenChange={handleOpenChange}>
      <ModalContent className="max-w-md">
        <ModalHeader>
          <ModalTitle className="flex items-center">
            <Zap className="h-5 w-5 mr-2 text-accent" />
            Index Repository
          </ModalTitle>
          <ModalDescription>
            Build semantic memory for a repository. This creates vector embeddings
            for intelligent search.
          </ModalDescription>
        </ModalHeader>

        <div className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium text-text">
              Select Repository
            </label>
            <select
              value={selectedRepo?.id || ""}
              onChange={(e) => {
                const repo = repositories.find(
                  (r) => r.id === e.target.value
                );
                setSelectedRepo(repo || null);
              }}
              className="w-full h-10 rounded-md border border-border bg-surface px-3 text-sm text-text focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
            >
              <option value="">Choose a repository...</option>
              {repositories.map((repo) => (
                <option key={repo.id} value={repo.id}>
                  {repo.name} ({repo.chunks_count || 0} chunks)
                </option>
              ))}
            </select>
          </div>

          {selectedRepo && (
            <div className="flex items-center justify-between rounded-lg border border-border bg-surface-hover p-3">
              <div className="flex items-center space-x-2">
                <RefreshCw className="h-4 w-4 text-text-muted" />
                <span className="text-sm text-text">Force Reindex</span>
              </div>
              <button
                onClick={() => setForceReindex(!forceReindex)}
                className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${
                  forceReindex ? "bg-accent" : "bg-surface"
                }`}
              >
                <span
                  className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white transition-transform ${
                    forceReindex ? "translate-x-4.5" : "translate-x-0.5"
                  }`}
                />
              </button>
            </div>
          )}

          {error && (
            <div className="flex items-center space-x-2 rounded-md bg-danger/10 p-3 text-sm text-danger">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {success && (
            <div className="flex items-center space-x-2 rounded-md bg-success/10 p-3 text-sm text-success">
              <Check className="h-4 w-4 shrink-0" />
              <span>Indexing completed successfully!</span>
            </div>
          )}
        </div>

        <ModalFooter>
          <Button
            variant="outline"
            onClick={() => handleOpenChange(false)}
            disabled={isIndexing}
          >
            Cancel
          </Button>
          <Button
            onClick={handleIndex}
            disabled={!selectedRepo || isIndexing || success}
            isLoading={isIndexing}
            leftIcon={<Zap className="h-4 w-4" />}
          >
            {isIndexing ? "Indexing..." : "Start Indexing"}
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
}
