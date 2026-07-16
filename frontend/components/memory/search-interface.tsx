"use client";

import * as React from "react";
import {
  Search,
  Zap,
  Clock,
  X,
  ChevronDown,
  Filter,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { useMemoryStore } from "@/stores/memory-store";
import type { ChunkType, IndexedRepository } from "@/types/memory";

interface SearchInterfaceProps {
  onSearch: (
    query: string,
    filters: {
      repository_id?: string;
      chunk_types?: ChunkType[];
      language?: string;
      framework?: string;
    }
  ) => void;
  onBuildContext: (query: string, repositoryId?: string) => void;
  isLoading: boolean;
  repositories: IndexedRepository[];
}

const CHUNK_TYPES: { value: ChunkType; label: string }[] = [
  { value: "repository", label: "Repository" },
  { value: "module", label: "Module" },
  { value: "class", label: "Class" },
  { value: "function", label: "Function" },
  { value: "route", label: "Route" },
  { value: "database", label: "Database" },
  { value: "config", label: "Config" },
  { value: "documentation", label: "Documentation" },
];

export function SearchInterface({
  onSearch,
  onBuildContext,
  isLoading,
  repositories,
}: SearchInterfaceProps) {
  const [query, setQuery] = React.useState("");
  const [showFilters, setShowFilters] = React.useState(false);
  const [selectedRepo, setSelectedRepo] = React.useState<string>("");
  const [selectedTypes, setSelectedTypes] = React.useState<ChunkType[]>([]);
  const [language, setLanguage] = React.useState("");
  const [framework, setFramework] = React.useState("");
  const inputRef = React.useRef<HTMLInputElement>(null);

  const { searchHistory, setLastQuery } = useMemoryStore();

  React.useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const toggleType = (type: ChunkType) => {
    setSelectedTypes((prev) =>
      prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type]
    );
  };

  const handleSearch = () => {
    if (!query.trim()) return;
    onSearch(query, {
      repository_id: selectedRepo || undefined,
      chunk_types: selectedTypes.length > 0 ? selectedTypes : undefined,
      language: language || undefined,
      framework: framework || undefined,
    });
  };

  const handleBuildContext = () => {
    if (!query.trim()) return;
    onBuildContext(query, selectedRepo || undefined);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSearch();
    }
  };

  const handleHistoryClick = (q: string) => {
    setQuery(q);
    setLastQuery(q);
    onSearch(q, {
      repository_id: selectedRepo || undefined,
      chunk_types: selectedTypes.length > 0 ? selectedTypes : undefined,
    });
  };

  const hasActiveFilters =
    selectedRepo || selectedTypes.length > 0 || language || framework;

  return (
    <div className="space-y-4">
      <div className="relative">
        <div className="relative flex items-center">
          <Search className="absolute left-4 h-5 w-5 text-text-muted pointer-events-none" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Search your codebase..."
            className="w-full h-14 pl-12 pr-64 rounded-xl border border-border bg-surface text-text placeholder:text-text-muted focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/20 text-base"
          />
          <div className="absolute right-2 flex items-center space-x-2">
            <select
              value={selectedRepo}
              onChange={(e) => setSelectedRepo(e.target.value)}
              className="h-8 rounded-md border border-border bg-surface px-2 text-xs text-text focus:border-accent focus:outline-none"
            >
              <option value="">All Projects</option>
              {repositories.map((repo) => (
                <option key={repo.id} value={repo.id}>
                  {repo.name}
                </option>
              ))}
            </select>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowFilters(!showFilters)}
              className={hasActiveFilters ? "text-accent" : "text-text-muted"}
            >
              <Filter className="h-4 w-4" />
              {hasActiveFilters && (
                <Badge
                  variant="secondary"
                  className="ml-1 h-5 min-w-5 text-xs"
                >
                  {[
                    selectedRepo ? 1 : 0,
                    selectedTypes.length,
                    language ? 1 : 0,
                    framework ? 1 : 0,
                  ].reduce((a, b) => a + b, 0)}
                </Badge>
              )}
            </Button>
            <Button
              onClick={handleSearch}
              disabled={!query.trim() || isLoading}
              isLoading={isLoading}
              size="sm"
              leftIcon={<Search className="h-4 w-4" />}
            >
              Search
            </Button>
          </div>
        </div>
      </div>

      {showFilters && (
        <div className="rounded-lg border border-border bg-surface p-4 space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-medium text-text">Filters</h4>
            {hasActiveFilters && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  setSelectedRepo("");
                  setSelectedTypes([]);
                  setLanguage("");
                  setFramework("");
                }}
              >
                Clear all
              </Button>
            )}
          </div>

          <div className="space-y-2">
            <label className="text-xs font-medium text-text-muted uppercase tracking-wide">
              Repository
            </label>
            <select
              value={selectedRepo}
              onChange={(e) => setSelectedRepo(e.target.value)}
              className="w-full h-9 rounded-md border border-border bg-surface px-3 text-sm text-text focus:border-accent focus:outline-none"
            >
              <option value="">All repositories</option>
              {repositories.map((repo) => (
                <option key={repo.id} value={repo.id}>
                  {repo.name}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-2">
            <label className="text-xs font-medium text-text-muted uppercase tracking-wide">
              Chunk Types
            </label>
            <div className="flex flex-wrap gap-2">
              {CHUNK_TYPES.map((type) => (
                <button
                  key={type.value}
                  onClick={() => toggleType(type.value)}
                  className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                    selectedTypes.includes(type.value)
                      ? "bg-accent text-white"
                      : "bg-surface-hover text-text-muted hover:text-text"
                  }`}
                >
                  {type.label}
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-xs font-medium text-text-muted uppercase tracking-wide">
                Language
              </label>
              <Input
                placeholder="e.g. TypeScript"
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="h-9"
              />
            </div>
            <div className="space-y-2">
              <label className="text-xs font-medium text-text-muted uppercase tracking-wide">
                Framework
              </label>
              <Input
                placeholder="e.g. Next.js"
                value={framework}
                onChange={(e) => setFramework(e.target.value)}
                className="h-9"
              />
            </div>
          </div>
        </div>
      )}

      {searchHistory.length > 0 && !query && (
        <div className="space-y-2">
          <h4 className="text-xs font-medium text-text-muted uppercase tracking-wide flex items-center">
            <Clock className="h-3 w-3 mr-1" />
            Recent Searches
          </h4>
          <div className="flex flex-wrap gap-2">
            {searchHistory.map((q, i) => (
              <button
                key={`${q}-${i}`}
                onClick={() => handleHistoryClick(q)}
                className="inline-flex items-center px-3 py-1 rounded-full bg-surface-hover text-xs text-text-muted hover:text-text transition-colors"
              >
                {q}
                <X className="h-3 w-3 ml-1 opacity-50" />
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="flex items-center space-x-2">
        <Button
          variant="outline"
          size="sm"
          onClick={handleBuildContext}
          disabled={!query.trim() || isLoading}
          leftIcon={<Zap className="h-4 w-4" />}
        >
          Build Context
        </Button>
        <span className="text-xs text-text-muted">
          Optimize context for AI consumption
        </span>
      </div>
    </div>
  );
}
