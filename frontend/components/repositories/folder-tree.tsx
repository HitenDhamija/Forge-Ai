"use client";

import * as React from "react";
import {
  ChevronRight,
  ChevronDown,
  Folder,
  FolderOpen,
  File,
  FileCode,
  FileText,
  FileJson,
  FileCog,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { FolderInfo } from "@/types/repository";

interface FolderTreeProps {
  folders: FolderInfo[];
  level?: number;
}

function getFileIcon(name: string): React.ReactNode {
  if (name.endsWith(".json")) return <FileJson className="h-4 w-4 text-warning" />;
  if (name.endsWith(".config") || name.endsWith(".rc") || name.startsWith("."))
    return <FileCog className="h-4 w-4 text-text-muted" />;
  if (
    name.endsWith(".ts") ||
    name.endsWith(".tsx") ||
    name.endsWith(".js") ||
    name.endsWith(".jsx")
  )
    return <FileCode className="h-4 w-4 text-accent" />;
  if (name.endsWith(".md") || name.endsWith(".txt"))
    return <FileText className="h-4 w-4 text-success" />;
  return <File className="h-4 w-4 text-text-muted" />;
}

function FolderNode({ folder, level = 0 }: { folder: FolderInfo; level: number }) {
  const [isExpanded, setIsExpanded] = React.useState(level < 1);
  const hasChildren = folder.children.length > 0;

  return (
    <div>
      <button
        onClick={() => hasChildren && setIsExpanded(!isExpanded)}
        className={cn(
          "flex w-full items-center space-x-2 rounded-md px-2 py-1 text-left text-sm transition-colors hover:bg-surface-hover",
          hasChildren ? "cursor-pointer" : "cursor-default"
        )}
        style={{ paddingLeft: `${level * 16 + 8}px` }}
      >
        {hasChildren ? (
          isExpanded ? (
            <ChevronDown className="h-4 w-4 shrink-0 text-text-muted" />
          ) : (
            <ChevronRight className="h-4 w-4 shrink-0 text-text-muted" />
          )
        ) : (
          <span className="h-4 w-4 shrink-0" />
        )}
        {isExpanded ? (
          <FolderOpen className="h-4 w-4 shrink-0 text-warning" />
        ) : (
          <Folder className="h-4 w-4 shrink-0 text-warning" />
        )}
        <span className="flex-1 truncate font-medium text-text">
          {folder.name}
        </span>
        {folder.purpose && (
          <span className="truncate text-xs text-text-muted">
            {folder.purpose}
          </span>
        )}
        <span className="shrink-0 text-xs text-text-muted">
          {folder.file_count} files
        </span>
      </button>
      {isExpanded && hasChildren && (
        <div>
          {folder.children.map((child) => (
            <FolderNode key={child.path} folder={child} level={level + 1} />
          ))}
        </div>
      )}
    </div>
  );
}

function FolderTree({ folders, level = 0 }: FolderTreeProps) {
  if (folders.length === 0) {
    return (
      <p className="text-sm text-text-muted">No folder structure available</p>
    );
  }

  return (
    <div className="rounded-md border border-border bg-surface p-2">
      {folders.map((folder) => (
        <FolderNode key={folder.path} folder={folder} level={level} />
      ))}
    </div>
  );
}

export { FolderTree };
