"use client";

import * as React from "react";
import {
  ChevronDown,
  ChevronUp,
  Hash,
  ExternalLink,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { SearchResult } from "@/types/memory";

interface SearchResultsProps {
  results: SearchResult[];
}

const TYPE_COLORS: Record<string, string> = {
  repository: "bg-blue-500/20 text-blue-400",
  module: "bg-purple-500/20 text-purple-400",
  class: "bg-green-500/20 text-green-400",
  function: "bg-yellow-500/20 text-yellow-400",
  route: "bg-pink-500/20 text-pink-400",
  database: "bg-orange-500/20 text-orange-400",
  config: "bg-cyan-500/20 text-cyan-400",
  documentation: "bg-gray-500/20 text-gray-400",
};

export function SearchResults({ results }: SearchResultsProps) {
  const [expandedResults, setExpandedResults] = React.useState<Set<number>>(
    new Set()
  );

  const toggleResult = (index: number) => {
    setExpandedResults((prev) => {
      const next = new Set(prev);
      if (next.has(index)) {
        next.delete(index);
      } else {
        next.add(index);
      }
      return next;
    });
  };

  if (results.length === 0) return null;

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-text">
          Search Results
        </h3>
        <span className="text-xs text-text-muted">
          {results.length} results found
        </span>
      </div>

      <div className="space-y-2">
        {results.map((result, index) => (
          <div
            key={`${result.chunk.id}-${index}`}
            className="rounded-lg border border-border bg-surface hover:border-accent/50 transition-colors"
          >
            <button
              onClick={() => toggleResult(index)}
              className="w-full text-left p-4"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2 mb-2">
                    <span className="text-xs font-mono text-text-muted">
                      #{result.rank}
                    </span>
                    <Badge
                      className={`text-xs ${
                        TYPE_COLORS[result.chunk.chunk_type] || ""
                      }`}
                    >
                      {result.chunk.chunk_type}
                    </Badge>
                    <span className="text-xs font-medium text-accent">
                      {(result.score * 100).toFixed(1)}%
                    </span>
                  </div>

                  <p className="text-sm text-text line-clamp-2">
                    {result.chunk.content.substring(0, 200)}
                    {result.chunk.content.length > 200 && "..."}
                  </p>

                  {result.explanation && (
                    <p className="mt-2 text-xs text-text-muted italic">
                      {result.explanation}
                    </p>
                  )}
                </div>

                <div className="ml-4 shrink-0">
                  {expandedResults.has(index) ? (
                    <ChevronUp className="h-4 w-4 text-text-muted" />
                  ) : (
                    <ChevronDown className="h-4 w-4 text-text-muted" />
                  )}
                </div>
              </div>
            </button>

            {expandedResults.has(index) && (
              <div className="px-4 pb-4 border-t border-border">
                <div className="mt-3 space-y-3">
                  <div>
                    <h4 className="text-xs font-medium text-text-muted mb-1">
                      Content
                    </h4>
                    <pre className="text-xs text-text bg-bg rounded-md p-3 overflow-auto max-h-48 whitespace-pre-wrap font-mono">
                      {result.chunk.content}
                    </pre>
                  </div>

                  <div>
                    <h4 className="text-xs font-medium text-text-muted mb-1">
                      Metadata
                    </h4>
                    <div className="flex flex-wrap gap-1">
                      {Object.entries(result.chunk.metadata).map(
                        ([key, value]) => (
                          <Badge
                            key={key}
                            variant="outline"
                            className="text-xs"
                          >
                            <Hash className="h-3 w-3 mr-1" />
                            {key}: {String(value)}
                          </Badge>
                        )
                      )}
                      {result.chunk.embedding_model && (
                        <Badge variant="outline" className="text-xs">
                          Model: {result.chunk.embedding_model}
                        </Badge>
                      )}
                      <Badge variant="outline" className="text-xs">
                        v{result.chunk.version}
                      </Badge>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2 text-xs text-text-muted">
                    <span>
                      Created:{" "}
                      {new Date(result.chunk.created_at).toLocaleDateString()}
                    </span>
                    <span>•</span>
                    <span>ID: {result.chunk.id.substring(0, 8)}</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
