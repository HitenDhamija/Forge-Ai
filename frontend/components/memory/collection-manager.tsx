"use client";

import * as React from "react";
import {
  Database,
  Trash2,
  AlertCircle,
  HardDrive,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import type { CollectionStats } from "@/types/memory";

interface CollectionManagerProps {
  collections: CollectionStats[];
}

function formatBytes(bytes: number | null): string {
  if (bytes === null || bytes === undefined) return "N/A";
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
}

export function CollectionManager({ collections }: CollectionManagerProps) {
  const [deletingCollection, setDeletingCollection] = React.useState<
    string | null
  >(null);

  if (collections.length === 0) {
    return (
      <EmptyState
        icon={<Database className="h-12 w-12" />}
        title="No collections"
        description="Collections are created when you index repositories."
      />
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-text">
          ChromaDB Collections
        </h3>
        <span className="text-xs text-text-muted">
          {collections.length} collections
        </span>
      </div>

      <div className="grid gap-3">
        {collections.map((collection) => (
          <Card
            key={collection.name}
            className="hover:border-accent/50 transition-colors"
          >
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3 min-w-0">
                  <div className="rounded-lg bg-surface-hover p-2">
                    <Database className="h-4 w-4 text-accent" />
                  </div>
                  <div className="min-w-0">
                    <h4 className="text-sm font-medium text-text truncate">
                      {collection.name}
                    </h4>
                    <div className="flex items-center space-x-3 mt-1">
                      <Badge variant="secondary" className="text-xs">
                        {collection.count} documents
                      </Badge>
                      <span className="text-xs text-text-muted flex items-center">
                        <HardDrive className="h-3 w-3 mr-1" />
                        {formatBytes(collection.size_bytes)}
                      </span>
                      {collection.last_updated && (
                        <span className="text-xs text-text-muted">
                          Updated:{" "}
                          {new Date(
                            collection.last_updated
                          ).toLocaleDateString()}
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                <div className="shrink-0">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() =>
                      setDeletingCollection(collection.name)
                    }
                    title="Delete collection"
                    className="text-text-muted hover:text-danger"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
