"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import {
  GitBranch,
  Trash2,
  FileCode,
  Loader2,
  AlertCircle,
  CheckCircle2,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { RepositoryInfo } from "@/types/repository";

interface RepositoryCardProps {
  repository: RepositoryInfo;
  languages?: { name: string; percentage: number }[];
  frameworks?: { name: string; confidence: number }[];
  onDelete?: (id: string) => void;
}

const STATUS_CONFIG: Record<
  RepositoryInfo["status"],
  { label: string; variant: "default" | "success" | "warning" | "destructive"; icon: React.ReactNode }
> = {
  ready: {
    label: "Ready",
    variant: "success",
    icon: <CheckCircle2 className="h-3 w-3" />,
  },
  analyzing: {
    label: "Analyzing",
    variant: "warning",
    icon: <Loader2 className="h-3 w-3 animate-spin" />,
  },
  importing: {
    label: "Importing",
    variant: "warning",
    icon: <Loader2 className="h-3 w-3 animate-spin" />,
  },
  error: {
    label: "Error",
    variant: "destructive",
    icon: <AlertCircle className="h-3 w-3" />,
  },
};

function RepositoryCard({
  repository,
  languages = [],
  frameworks = [],
  onDelete,
}: RepositoryCardProps) {
  const router = useRouter();
  const statusConfig = STATUS_CONFIG[repository.status] || {
    label: repository.status,
    variant: "default" as const,
    icon: <AlertCircle className="h-3 w-3" />,
  };

  const handleClick = () => {
    router.push(`/repositories/${repository.id}`);
  };

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    onDelete?.(repository.id);
  };

  return (
    <Card
      className="group cursor-pointer transition-colors hover:border-text-muted"
      onClick={handleClick}
    >
      <CardHeader className="flex flex-row items-start justify-between space-y-0">
        <div className="flex items-center space-x-3">
          <div className="rounded-md bg-surface-hover p-2">
            <GitBranch className="h-5 w-5 text-accent" />
          </div>
          <div className="space-y-1">
            <CardTitle className="text-lg">{repository.name}</CardTitle>
            <p className="line-clamp-1 text-sm text-text-muted">
              {repository.description || "No description"}
            </p>
          </div>
        </div>
        {onDelete && (
          <Button
            variant="ghost"
            size="icon"
            className="opacity-0 group-hover:opacity-100 text-text-muted hover:text-danger"
            onClick={handleDelete}
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        )}
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          <div className="flex items-center space-x-2">
            <Badge variant={statusConfig.variant} className="gap-1">
              {statusConfig.icon}
              {statusConfig.label}
            </Badge>
            <Badge variant="secondary" className="gap-1">
              <FileCode className="h-3 w-3" />
              {repository.import_method}
            </Badge>
          </div>

          {languages.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {languages.slice(0, 3).map((lang) => (
                <Badge key={lang.name} variant="default" className="text-xs">
                  {lang.name}
                </Badge>
              ))}
              {languages.length > 3 && (
                <Badge variant="default" className="text-xs">
                  +{languages.length - 3}
                </Badge>
              )}
            </div>
          )}

          {frameworks.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {frameworks.map((fw) => (
                <Badge key={fw.name} variant="secondary" className="text-xs">
                  {fw.name}
                </Badge>
              ))}
            </div>
          )}

          <div className="text-xs text-text-muted">
            Created {new Date(repository.created_at).toLocaleDateString()}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export { RepositoryCard };
