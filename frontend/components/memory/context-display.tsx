"use client";

import * as React from "react";
import {
  Copy,
  Check,
  ChevronDown,
  ChevronUp,
  Zap,
  Clock,
  Hash,
  Tag,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import type { ContextResponse } from "@/types/memory";

interface ContextDisplayProps {
  response: ContextResponse;
}

export function ContextDisplay({ response }: ContextDisplayProps) {
  const [copied, setCopied] = React.useState(false);
  const [expandedChunks, setExpandedChunks] = React.useState<Set<number>>(
    new Set()
  );

  const handleCopy = async () => {
    await navigator.clipboard.writeText(response.context);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const toggleChunk = (index: number) => {
    setExpandedChunks((prev) => {
      const next = new Set(prev);
      if (next.has(index)) {
        next.delete(index);
      } else {
        next.add(index);
      }
      return next;
    });
  };

  return (
    <div className="flex flex-col h-full space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-text flex items-center">
          <Zap className="h-4 w-4 mr-2 text-accent" />
          Generated Context
        </h3>
        <Button
          variant="outline"
          size="sm"
          onClick={handleCopy}
          leftIcon={
            copied ? (
              <Check className="h-4 w-4 text-success" />
            ) : (
              <Copy className="h-4 w-4" />
            )
          }
        >
          {copied ? "Copied!" : "Copy"}
        </Button>
      </div>

      <div className="flex items-center space-x-4 text-xs text-text-muted">
        <span className="flex items-center">
          <Tag className="h-3 w-3 mr-1" />
          {response.query_classification || "General"}
        </span>
        <span className="flex items-center">
          <Hash className="h-3 w-3 mr-1" />
          {response.token_count} tokens
        </span>
        <span className="flex items-center">
          <Clock className="h-3 w-3 mr-1" />
          {response.build_time_ms}ms
        </span>
      </div>

      <div className="flex-1 overflow-auto rounded-lg border border-border bg-bg p-4">
        <pre className="text-sm text-text whitespace-pre-wrap font-mono leading-relaxed">
          {response.context}
        </pre>
      </div>

      {(response.chunks_used?.length ?? 0) > 0 && (
        <div className="space-y-2">
          <h4 className="text-xs font-medium text-text-muted uppercase tracking-wide">
            Chunks Used ({response.chunks_used.length})
          </h4>
          <div className="space-y-2 max-h-60 overflow-auto">
            {response.chunks_used.map((item, index) => (
              <div
                key={`${item.chunk.id}-${index}`}
                className="rounded-lg border border-border bg-surface"
              >
                <button
                  onClick={() => toggleChunk(index)}
                  className="w-full flex items-center justify-between p-3 text-left"
                >
                  <div className="flex items-center space-x-3 min-w-0">
                    <Badge
                      variant={
                        item.chunk.chunk_type === "function"
                          ? "default"
                          : item.chunk.chunk_type === "class"
                          ? "secondary"
                          : "outline"
                      }
                      className="shrink-0"
                    >
                      {item.chunk.chunk_type}
                    </Badge>
                    <span className="text-sm text-text truncate">
                      {item.chunk.content.substring(0, 80)}...
                    </span>
                  </div>
                  <div className="flex items-center space-x-2 shrink-0">
                    <span className="text-xs text-accent">
                      {(item.score * 100).toFixed(1)}%
                    </span>
                    {expandedChunks.has(index) ? (
                      <ChevronUp className="h-4 w-4 text-text-muted" />
                    ) : (
                      <ChevronDown className="h-4 w-4 text-text-muted" />
                    )}
                  </div>
                </button>
                {expandedChunks.has(index) && (
                  <div className="px-3 pb-3 border-t border-border">
                    <pre className="mt-2 text-xs text-text-muted whitespace-pre-wrap font-mono">
                      {item.chunk.content}
                    </pre>
                    {Object.keys(item.chunk.metadata).length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1">
                        {Object.entries(item.chunk.metadata).map(
                          ([key, value]) => (
                            <Badge
                              key={key}
                              variant="outline"
                              className="text-xs"
                            >
                              {key}: {String(value)}
                            </Badge>
                          )
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
