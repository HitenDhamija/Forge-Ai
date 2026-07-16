"use client";

import * as React from "react";
import {
  BarChart3,
  Database,
  Cpu,
  Ruler,
  HardDrive,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { MemoryStats } from "@/types/memory";

interface VectorStatsProps {
  stats: MemoryStats | null;
}

function formatBytes(bytes: number | null): string {
  if (bytes === null || bytes === undefined) return "N/A";
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
}

export function VectorStats({ stats }: VectorStatsProps) {
  if (!stats) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm flex items-center">
            <BarChart3 className="h-4 w-4 mr-2" />
            Vector Statistics
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-text-muted">Loading statistics...</p>
        </CardContent>
      </Card>
    );
  }

  const statItems = [
    {
      icon: <Database className="h-4 w-4" />,
      label: "Total Chunks",
      value: stats.total_chunks.toLocaleString(),
    },
    {
      icon: <Database className="h-4 w-4" />,
      label: "Repositories",
      value: stats.total_repositories.toLocaleString(),
    },
    {
      icon: <Cpu className="h-4 w-4" />,
      label: "Embedding Model",
      value: stats.embedding_model,
    },
    {
      icon: <Ruler className="h-4 w-4" />,
      label: "Dimensions",
      value: stats.embedding_dimension?.toLocaleString() ?? "0",
    },
    {
      icon: <HardDrive className="h-4 w-4" />,
      label: "Storage Size",
      value: formatBytes(stats.storage_size_bytes),
    },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm flex items-center">
          <BarChart3 className="h-4 w-4 mr-2" />
          Vector Statistics
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {statItems.map((item) => (
          <div
            key={item.label}
            className="flex items-center justify-between"
          >
            <div className="flex items-center space-x-2 text-text-muted">
              {item.icon}
              <span className="text-sm">{item.label}</span>
            </div>
            <span className="text-sm font-medium text-text">{item.value}</span>
          </div>
        ))}

        {stats.collections.length > 0 && (
          <div className="pt-4 border-t border-border">
            <h4 className="text-xs font-medium text-text-muted uppercase tracking-wide mb-3">
              Collection Breakdown
            </h4>
            <div className="space-y-2">
              {stats.collections.map((col) => (
                <div
                  key={col.name}
                  className="flex items-center justify-between text-xs"
                >
                  <span className="text-text-muted truncate flex-1 mr-2">
                    {col.name}
                  </span>
                  <Badge variant="outline" className="text-xs shrink-0">
                    {col.count}
                  </Badge>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
