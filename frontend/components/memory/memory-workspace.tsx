"use client";

import * as React from "react";
import { Database, Search, Zap, BarChart3 } from "lucide-react";
import { useMemoryStore } from "@/stores/memory-store";
import { memoryService } from "@/services/memory.service";
import { SearchInterface } from "./search-interface";
import { SearchResults } from "./search-results";
import { ContextDisplay } from "./context-display";
import { IndexedRepositories } from "./indexed-repositories";
import { VectorStats } from "./vector-stats";
import { CollectionManager } from "./collection-manager";
import { IndexModal } from "./index-modal";
import { Button } from "@/components/ui/button";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import { ErrorState } from "@/components/ui/error-state";
import type {
  SearchRequest,
  ContextRequest,
  ChunkType,
} from "@/types/memory";

export function MemoryWorkspace() {
  const {
    searchResults,
    contextResponse,
    memoryStats,
    indexedRepositories,
    collections,
    isSearching,
    isIndexing,
    isLoading,
    error,
    setSearchResults,
    setContextResponse,
    setMemoryStats,
    setIndexedRepositories,
    setCollections,
    setSearching,
    setIndexing,
    setLoading,
    setError,
    clearError,
    addToHistory,
    lastQuery,
    setLastQuery,
  } = useMemoryStore();

  const [indexModalOpen, setIndexModalOpen] = React.useState(false);
  const [activeTab, setActiveTab] = React.useState("search");

  const loadInitialData = React.useCallback(async () => {
    setLoading(true);
    clearError();
    try {
      const [statsResult, reposResult] = await Promise.allSettled([
        memoryService.getStats(),
        memoryService.listRepositories(),
      ]);

      if (statsResult.status === "fulfilled") {
        setMemoryStats(statsResult.value.data);
        if (statsResult.value.data?.collections) {
          setCollections(statsResult.value.data.collections);
        }
      } else {
        console.error("Failed to load memory stats:", statsResult.reason);
      }

      if (reposResult.status === "fulfilled") {
        setIndexedRepositories(reposResult.value.data);
      } else {
        console.error("Failed to load repositories:", reposResult.reason);
      }

      if (statsResult.status === "rejected" && reposResult.status === "rejected") {
        setError("Failed to load memory data. Is the backend server running on port 8000?");
      }
    } catch (err: any) {
      setError(err.message || "Failed to load memory data");
    } finally {
      setLoading(false);
    }
  }, [
    setLoading,
    clearError,
    setMemoryStats,
    setIndexedRepositories,
    setCollections,
    setError,
  ]);

  React.useEffect(() => {
    loadInitialData();
  }, [loadInitialData]);

  // Auto-index repositories that aren't indexed yet
  React.useEffect(() => {
    const autoIndex = async () => {
      try {
        const reposRes = await fetch("http://127.0.0.1:8000/api/v1/repositories");
        const reposData = await reposRes.json();
        const repos = reposData?.data || [];
        const indexedIds = new Set(indexedRepositories.map((r: any) => r.id));

        for (const repo of repos) {
          if (!indexedIds.has(repo.id)) {
            try {
              await memoryService.index({
                repository_id: repo.id,
                repository_name: repo.name,
                force_reindex: false,
              });
            } catch {}
          }
        }
        // Reload stats after auto-indexing
        if (repos.length > 0) {
          const statsResult = await memoryService.getStats();
          setMemoryStats(statsResult.data);
          const reposResult = await memoryService.listRepositories();
          setIndexedRepositories(reposResult.data);
        }
      } catch {}
    };
    if (indexedRepositories.length === 0) {
      autoIndex();
    }
  }, [indexedRepositories.length > 0]);

  const handleSearch = React.useCallback(
    async (
      query: string,
      filters: {
        repository_id?: string;
        chunk_types?: ChunkType[];
        language?: string;
        framework?: string;
      }
    ) => {
      if (!query.trim()) return;
      setSearching(true);
      setError(null);
      setLastQuery(query);
      addToHistory(query);
      try {
        const request: SearchRequest = {
          query: query.trim(),
          top_k: 20,
          similarity_threshold: 0.3,
          ...filters,
        };
        console.log("Search request:", request);
        const response = await memoryService.search(request);
        console.log("Search response full:", response);
        console.log("Search response.data:", response.data);
        console.log("Search response.data.results:", response.data.results);
        setSearchResults(response.data.results);
        console.log("setSearchResults called with:", response.data.results?.length, "results");
      } catch (err: any) {
        console.error("Search error:", err);
        setError(err.response?.data?.detail || "Search failed");
      } finally {
        setSearching(false);
      }
    },
    [setSearching, setError, setLastQuery, addToHistory, setSearchResults]
  );

  const handleBuildContext = React.useCallback(
    async (query: string, repositoryId?: string, maxTokens?: number) => {
      if (!query.trim()) return;
      setSearching(true);
      setError(null);
      try {
        const request: ContextRequest = {
          query: query.trim(),
          repository_id: repositoryId,
          max_tokens: maxTokens || 4000,
        };
        const response = await memoryService.getContext(request);
        setContextResponse(response.data);
      } catch (err: any) {
        setError(err.response?.data?.detail || "Failed to build context");
      } finally {
        setSearching(false);
      }
    },
    [setSearching, setError, setContextResponse]
  );

  const handleIndex = React.useCallback(
    async (
      repositoryId: string,
      repositoryName: string,
      forceReindex: boolean
    ) => {
      console.log("Indexing:", repositoryId, repositoryName, forceReindex);
      setIndexing(true);
      setError(null);
      try {
        await memoryService.index({
          repository_id: repositoryId,
          repository_name: repositoryName,
          force_reindex: forceReindex,
        });
        console.log("Indexing completed, reloading data...");
        await loadInitialData();
      } catch (err: any) {
        console.error("Indexing error:", err);
        setError(err.response?.data?.detail || "Indexing failed");
        throw err;
      } finally {
        setIndexing(false);
      }
    },
    [setIndexing, setError, loadInitialData]
  );

  const handleDeleteRepository = React.useCallback(
    async (id: string) => {
      try {
        await memoryService.deleteRepository(id);
        await loadInitialData();
      } catch (err: any) {
        setError(
          err.response?.data?.detail || "Failed to delete repository"
        );
      }
    },
    [loadInitialData, setError]
  );

  if (isLoading && !isIndexing) {
    return (
      <div className="flex flex-col h-full p-6 space-y-6">
        <div className="flex items-center space-x-3">
          <Skeleton variant="circular" className="h-8 w-8" />
          <Skeleton className="h-8 w-48" />
        </div>
        <div className="grid grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
        <div className="flex-1 grid grid-cols-2 gap-6">
          <Skeleton className="h-full" />
          <Skeleton className="h-full" />
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-6 py-4 border-b border-border">
        <div className="flex items-center space-x-3">
          <div className="rounded-lg bg-accent/10 p-2">
            <Database className="h-5 w-5 text-accent" />
          </div>
          <div>
            <h1 className="text-xl font-semibold text-text">
              Semantic Memory
            </h1>
            <p className="text-sm text-text-muted">
              Search and manage your codebase knowledge
            </p>
          </div>
        </div>
        <Button
          onClick={() => setIndexModalOpen(true)}
          leftIcon={<Zap className="h-4 w-4" />}
        >
          Index Repository
        </Button>
      </div>

      <div className="grid grid-cols-4 gap-4 px-6 py-4 border-b border-border">
        <StatCard
          icon={<BarChart3 className="h-4 w-4" />}
          label="Total Chunks"
          value={memoryStats?.total_chunks || 0}
        />
        <StatCard
          icon={<Database className="h-4 w-4" />}
          label="Repositories"
          value={memoryStats?.total_repositories || 0}
        />
        <StatCard
          icon={<Search className="h-4 w-4" />}
          label="Embedding Model"
          value={memoryStats?.embedding_model || "N/A"}
        />
        <StatCard
          icon={<Zap className="h-4 w-4" />}
          label="Dimensions"
          value={memoryStats?.embedding_dimension || 0}
        />
      </div>

      {error && (
        <div className="mx-6 mt-4">
          <ErrorState title="Error" description={error} onRetry={clearError} />
        </div>
      )}

      <div className="flex-1 overflow-hidden px-6 py-4">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="h-full flex flex-col">
          <TabsList>
            <TabsTrigger value="search">
              <Search className="h-4 w-4 mr-2" />
              Search
            </TabsTrigger>
            <TabsTrigger value="repositories">
              <Database className="h-4 w-4 mr-2" />
              Repositories
            </TabsTrigger>
            <TabsTrigger value="collections">
              <BarChart3 className="h-4 w-4 mr-2" />
              Collections
            </TabsTrigger>
          </TabsList>

          <TabsContent value="search" className="flex-1 mt-4 overflow-auto">
            <div className="grid grid-cols-2 gap-6" style={{minHeight: "400px"}}>
              <div className="flex flex-col space-y-4">
                <SearchInterface
                  onSearch={handleSearch}
                  onBuildContext={handleBuildContext}
                  isLoading={isSearching}
                  repositories={indexedRepositories}
                />
                {isSearching && (
                  <div className="text-center py-8 text-text-muted">
                    <p className="text-sm">Searching...</p>
                  </div>
                )}
                {!isSearching && searchResults.length > 0 && (
                  <SearchResults results={searchResults} />
                )}
                {!isSearching && lastQuery && searchResults.length === 0 && !error && (
                  <div className="text-center py-8 text-text-muted">
                    <p className="text-sm">No results found for "{lastQuery}"</p>
                  </div>
                )}
              </div>
              <div className="overflow-auto">
                {contextResponse ? (
                  <ContextDisplay response={contextResponse} />
                ) : (
                  <div className="h-full flex items-center justify-center text-text-muted">
                    <div className="text-center">
                      <Search className="h-12 w-12 mx-auto mb-4 opacity-50" />
                      <p className="text-sm">
                        Run a search to see context
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </TabsContent>

          <TabsContent value="repositories" className="flex-1 mt-4 overflow-auto">
            <IndexedRepositories
              repositories={indexedRepositories}
              onDelete={handleDeleteRepository}
              onReindex={(repo) => {
                handleIndex(repo.id, repo.name, true);
              }}
            />
          </TabsContent>

          <TabsContent value="collections" className="flex-1 mt-4 overflow-auto">
            <div className="grid grid-cols-2 gap-6">
              <VectorStats stats={memoryStats} />
              <CollectionManager collections={collections} />
            </div>
          </TabsContent>
        </Tabs>
      </div>

      <IndexModal
        open={indexModalOpen}
        onOpenChange={setIndexModalOpen}
        onIndex={handleIndex}
        isIndexing={isIndexing}
        repositories={indexedRepositories}
      />
    </div>
  );
}

function StatCard({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: string | number;
}) {
  return (
    <div className="rounded-lg border border-border bg-surface p-4">
      <div className="flex items-center space-x-2 text-text-muted mb-2">
        {icon}
        <span className="text-xs font-medium">{label}</span>
      </div>
      <p className="text-lg font-semibold text-text truncate">{value}</p>
    </div>
  );
}
