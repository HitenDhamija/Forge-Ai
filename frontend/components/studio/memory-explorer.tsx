'use client';

import { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Skeleton } from '@/components/ui/skeleton';
import { EmptyState } from '@/components/ui/empty-state';
import { Button } from '@/components/ui/button';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import {
  Brain,
  Search,
  Database,
  FileCode,
  Layers,
  BarChart3,
  Clock,
  Tag,
  FolderOpen,
  Cpu,
  TrendingUp,
  Hash,
  ChevronRight,
  RefreshCw,
  Filter,
  Link2,
  Code,
  Globe,
  Cog,
  Loader2,
} from 'lucide-react';

type ChunkType = 'code' | 'documentation' | 'config' | 'test' | 'metadata';

interface MemoryChunk {
  id: string;
  content: string;
  filePath: string;
  language: string;
  framework: string;
  tags: string[];
  chunkType: ChunkType;
  repository: string;
  collection: string;
  similarity: number;
  tokens: number;
  createdAt: string;
  relatedChunks: string[];
}

interface Collection {
  id: string;
  name: string;
  chunkCount: number;
  repositories: { name: string; count: number }[];
  storageBytes: number;
}

interface MemoryStats {
  totalChunks: number;
  repositories: number;
  collections: number;
  searchCount: number;
  embeddingModel: string;
  embeddingDimensions: number;
  cacheHitRate: number;
}

const CHUNK_TYPE_CONFIG: Record<ChunkType, { label: string; variant: 'default' | 'secondary' | 'success' | 'warning' | 'outline'; icon: React.ReactNode }> = {
  code: { label: 'Code', variant: 'default', icon: <Code className="h-3 w-3" /> },
  documentation: { label: 'Docs', variant: 'success', icon: <FileCode className="h-3 w-3" /> },
  config: { label: 'Config', variant: 'secondary', icon: <Cog className="h-3 w-3" /> },
  test: { label: 'Test', variant: 'warning', icon: <FileCode className="h-3 w-3" /> },
  metadata: { label: 'Meta', variant: 'outline', icon: <Tag className="h-3 w-3" /> },
};

const MOCK_STATS: MemoryStats = {
  totalChunks: 12483,
  repositories: 8,
  collections: 5,
  searchCount: 3421,
  embeddingModel: 'text-embedding-3-small',
  embeddingDimensions: 1536,
  cacheHitRate: 0.847,
};

const MOCK_COLLECTIONS: Collection[] = [
  {
    id: 'col-1',
    name: 'forge-ai-backend',
    chunkCount: 4521,
    repositories: [
      { name: 'forge-ai/backend', count: 3201 },
      { name: 'forge-ai/shared', count: 1320 },
    ],
    storageBytes: 18432000,
  },
  {
    id: 'col-2',
    name: 'forge-ai-frontend',
    chunkCount: 3847,
    repositories: [
      { name: 'forge-ai/frontend', count: 3847 },
    ],
    storageBytes: 15360000,
  },
  {
    id: 'col-3',
    name: 'documentation',
    chunkCount: 2134,
    repositories: [
      { name: 'forge-ai/docs', count: 1890 },
      { name: 'forge-ai/frontend', count: 244 },
    ],
    storageBytes: 8192000,
  },
  {
    id: 'col-4',
    name: 'configuration',
    chunkCount: 1205,
    repositories: [
      { name: 'forge-ai/backend', count: 512 },
      { name: 'forge-ai/frontend', count: 445 },
      { name: 'forge-ai/infra', count: 248 },
    ],
    storageBytes: 4915200,
  },
  {
    id: 'col-5',
    name: 'test-suites',
    chunkCount: 776,
    repositories: [
      { name: 'forge-ai/backend', count: 401 },
      { name: 'forge-ai/frontend', count: 375 },
    ],
    storageBytes: 3072000,
  },
];

const MOCK_CHUNKS: MemoryChunk[] = [
  {
    id: 'chunk-1',
    content: `export class MemoryService {\n  private embeddingClient: EmbeddingClient;\n  private vectorStore: VectorStore;\n\n  async embedDocument(doc: Document): Promise<EmbeddingResult> {\n    const chunks = this.chunkDocument(doc);\n    const embeddings = await this.embeddingClient.embed(chunks);\n    await this.vectorStore.store(chunks, embeddings);\n    return { chunks: chunks.length, dimensions: embeddings[0].length };\n  }\n\n  private chunkDocument(doc: Document): string[] {\n    const maxTokens = 512;\n    const overlap = 50;\n    // ... chunking logic\n  }\n}`,
    filePath: 'packages/backend/src/services/memory.service.ts',
    language: 'TypeScript',
    framework: 'NestJS',
    tags: ['embeddings', 'vector-store', 'chunking'],
    chunkType: 'code',
    repository: 'forge-ai/backend',
    collection: 'forge-ai-backend',
    similarity: 0.94,
    tokens: 186,
    createdAt: '2025-06-28T14:22:00Z',
    relatedChunks: ['chunk-2', 'chunk-3', 'chunk-5'],
  },
  {
    id: 'chunk-2',
    content: `The Memory Explorer provides semantic search capabilities across all indexed repositories. Chunks are stored as vector embeddings and can be queried using natural language. The system supports filtering by repository, language, and chunk type.`,
    filePath: 'docs/features/memory-explorer.md',
    language: 'Markdown',
    framework: '',
    tags: ['memory', 'search', 'documentation'],
    chunkType: 'documentation',
    repository: 'forge-ai/docs',
    collection: 'documentation',
    similarity: 0.91,
    tokens: 62,
    createdAt: '2025-06-25T10:15:00Z',
    relatedChunks: ['chunk-1', 'chunk-4'],
  },
  {
    id: 'chunk-3',
    content: `interface ChunkMetadata {\n  filePath: string;\n  language: string;\n  framework?: string;\n  tags: string[];\n  chunkType: 'code' | 'documentation' | 'config' | 'test' | 'metadata';\n  repository: string;\n  collection: string;\n  tokens: number;\n  createdAt: Date;\n}`,
    filePath: 'packages/shared/src/types/memory.ts',
    language: 'TypeScript',
    framework: '',
    tags: ['types', 'interfaces', 'memory'],
    chunkType: 'code',
    repository: 'forge-ai/shared',
    collection: 'forge-ai-backend',
    similarity: 0.88,
    tokens: 94,
    createdAt: '2025-06-20T09:30:00Z',
    relatedChunks: ['chunk-1', 'chunk-5'],
  },
  {
    id: 'chunk-4',
    content: `test('should embed and retrieve chunks', async () => {\n  const service = new MemoryService(mockEmbedding, mockStore);\n  const doc = createTestDocument();\n  const result = await service.embedDocument(doc);\n  expect(result.chunks).toBeGreaterThan(0);\n\n  const results = await service.search('embedding', { limit: 5 });\n  expect(results).toHaveLength(5);\n  expect(results[0].similarity).toBeGreaterThan(0.8);\n});`,
    filePath: 'packages/backend/src/__tests__/memory.service.test.ts',
    language: 'TypeScript',
    framework: 'Vitest',
    tags: ['testing', 'memory', 'embeddings'],
    chunkType: 'test',
    repository: 'forge-ai/backend',
    collection: 'test-suites',
    similarity: 0.85,
    tokens: 108,
    createdAt: '2025-06-27T16:45:00Z',
    relatedChunks: ['chunk-1', 'chunk-3'],
  },
  {
    id: 'chunk-5',
    content: `MEMORY_EMBEDDING_MODEL=text-embedding-3-small\nMEMORY_EMBEDDING_DIMENSIONS=1536\nMEMORY_VECTOR_STORE=qdrant\nMEMORY_CHUNK_MAX_TOKENS=512\nMEMORY_CHUNK_OVERLAP=50\nMEMORY_CACHE_TTL=3600\nMEMORY_CACHE_MAX_SIZE=10000`,
    filePath: 'packages/backend/.env.example',
    language: 'Shell',
    framework: '',
    tags: ['config', 'environment', 'embeddings'],
    chunkType: 'config',
    repository: 'forge-ai/backend',
    collection: 'configuration',
    similarity: 0.79,
    tokens: 58,
    createdAt: '2025-06-15T11:00:00Z',
    relatedChunks: ['chunk-1', 'chunk-3'],
  },
];

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

function SimilarityBar({ score }: { score: number }) {
  const percent = Math.round(score * 100);
  const color =
    percent >= 90 ? 'bg-success' : percent >= 75 ? 'bg-info' : percent >= 50 ? 'bg-warning' : 'bg-danger';

  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-surface-hover">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${percent}%` }} />
      </div>
      <span className="text-xs font-medium text-text-muted">{percent}%</span>
    </div>
  );
}

function StatsOverview({ stats, isLoading }: { stats: MemoryStats; isLoading: boolean }) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
        {Array.from({ length: 6 }).map((_, i) => (
          <Card key={i}>
            <CardContent className="p-4">
              <Skeleton className="mb-2 h-3 w-20" />
              <Skeleton className="h-6 w-16" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-2 text-text-muted">
            <Brain className="h-4 w-4" />
            <span className="text-xs font-medium">Total Chunks</span>
          </div>
          <p className="mt-1 text-2xl font-bold text-text">{stats.totalChunks.toLocaleString()}</p>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-2 text-text-muted">
            <FolderOpen className="h-4 w-4" />
            <span className="text-xs font-medium">Repositories</span>
          </div>
          <p className="mt-1 text-2xl font-bold text-text">{stats.repositories}</p>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-2 text-text-muted">
            <Layers className="h-4 w-4" />
            <span className="text-xs font-medium">Collections</span>
          </div>
          <p className="mt-1 text-2xl font-bold text-text">{stats.collections}</p>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-2 text-text-muted">
            <Search className="h-4 w-4" />
            <span className="text-xs font-medium">Searches</span>
          </div>
          <p className="mt-1 text-2xl font-bold text-text">{stats.searchCount.toLocaleString()}</p>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-2 text-text-muted">
            <Cpu className="h-4 w-4" />
            <span className="text-xs font-medium">Embedding Model</span>
          </div>
          <p className="mt-1 truncate text-sm font-bold text-text">{stats.embeddingModel}</p>
          <p className="text-xs text-text-muted">{stats.embeddingDimensions}d</p>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-2 text-text-muted">
            <TrendingUp className="h-4 w-4" />
            <span className="text-xs font-medium">Cache Hit Rate</span>
          </div>
          <p className="mt-1 text-2xl font-bold text-success">{Math.round(stats.cacheHitRate * 100)}%</p>
        </CardContent>
      </Card>
    </div>
  );
}

function SearchPanel({
  chunks,
  selectedChunk,
  onSelectChunk,
  isLoading,
}: {
  chunks: MemoryChunk[];
  selectedChunk: MemoryChunk | null;
  onSelectChunk: (chunk: MemoryChunk) => void;
  isLoading: boolean;
}) {
  const [query, setQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState<ChunkType | 'all'>('all');
  const [repoFilter, setRepoFilter] = useState<string>('all');

  const filteredChunks = chunks.filter((chunk) => {
    const matchesQuery =
      !query ||
      chunk.content.toLowerCase().includes(query.toLowerCase()) ||
      chunk.filePath.toLowerCase().includes(query.toLowerCase()) ||
      chunk.tags.some((t) => t.toLowerCase().includes(query.toLowerCase()));
    const matchesType = typeFilter === 'all' || chunk.chunkType === typeFilter;
    const matchesRepo = repoFilter === 'all' || chunk.repository === repoFilter;
    return matchesQuery && matchesType && matchesRepo;
  });

  const repositories = Array.from(new Set(chunks.map((c) => c.repository)));

  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-border p-4">
        <h2 className="mb-3 text-sm font-semibold uppercase text-text-muted">Semantic Search</h2>
        <div className="space-y-3">
          <Input
            placeholder="Search chunks..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            leftIcon={<Search className="h-4 w-4" />}
          />
          <div className="flex gap-2">
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value as ChunkType | 'all')}
              className="flex h-8 flex-1 items-center rounded-md border border-border bg-surface px-2 text-xs text-text focus:border-accent focus:outline-none"
            >
              <option value="all">All Types</option>
              {Object.entries(CHUNK_TYPE_CONFIG).map(([key, cfg]) => (
                <option key={key} value={key}>
                  {cfg.label}
                </option>
              ))}
            </select>
            <select
              value={repoFilter}
              onChange={(e) => setRepoFilter(e.target.value)}
              className="flex h-8 flex-1 items-center rounded-md border border-border bg-surface px-2 text-xs text-text focus:border-accent focus:outline-none"
            >
              <option value="all">All Repos</option>
              {repositories.map((repo) => (
                <option key={repo} value={repo}>
                  {repo}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="space-y-2 p-3">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="space-y-2 rounded-lg border border-border p-3">
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-3 w-1/2" />
                <Skeleton className="h-1.5 w-full" />
              </div>
            ))}
          </div>
        ) : filteredChunks.length === 0 ? (
          <EmptyState
            icon={<Search className="h-10 w-10" />}
            title="No chunks found"
            description={query ? 'Try a different search term or adjust filters' : 'No chunks indexed yet'}
          />
        ) : (
          <div className="space-y-2 p-3">
            {filteredChunks.map((chunk) => {
              const isSelected = selectedChunk?.id === chunk.id;
              const typeConfig = CHUNK_TYPE_CONFIG[chunk.chunkType];
              return (
                <button
                  key={chunk.id}
                  onClick={() => onSelectChunk(chunk)}
                  className={`w-full rounded-lg border p-3 text-left transition-colors ${
                    isSelected
                      ? 'border-accent/30 bg-accent/10'
                      : 'border-border hover:bg-surface-hover'
                  }`}
                >
                  <div className="mb-1 flex items-center gap-2">
                    <Badge variant={typeConfig.variant} className="gap-1 text-[10px]">
                      {typeConfig.icon}
                      {typeConfig.label}
                    </Badge>
                    <span className="truncate text-xs text-text-muted">{chunk.filePath}</span>
                  </div>
                  <p className="mb-2 line-clamp-2 text-xs text-text">{chunk.content}</p>
                  <SimilarityBar score={chunk.similarity} />
                  <div className="mt-1 flex items-center gap-2 text-[10px] text-text-muted">
                    <span>{chunk.repository}</span>
                    <span>·</span>
                    <span>{chunk.tokens} tokens</span>
                  </div>
                </button>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

function ChunkViewer({ chunk }: { chunk: MemoryChunk }) {
  if (!chunk) {
    return (
      <div className="flex h-full items-center justify-center">
        <EmptyState
          icon={<Brain className="h-12 w-12" />}
          title="Select a chunk"
          description="Click on a search result to view its details"
        />
      </div>
    );
  }

  const typeConfig = CHUNK_TYPE_CONFIG[chunk.chunkType];

  return (
    <div className="flex h-full flex-col overflow-hidden border-l border-border">
      <div className="border-b border-border p-4">
        <div className="mb-2 flex items-center gap-2">
          <Badge variant={typeConfig.variant} className="gap-1">
            {typeConfig.icon}
            {typeConfig.label}
          </Badge>
          <span className="text-sm font-medium text-text">{chunk.id}</span>
        </div>
        <p className="text-xs text-text-muted">{chunk.filePath}</p>
      </div>

      <div className="flex-1 overflow-y-auto">
        <Tabs defaultValue="content" className="h-full">
          <div className="border-b border-border px-4">
            <TabsList>
              <TabsTrigger value="content">Content</TabsTrigger>
              <TabsTrigger value="metadata">Metadata</TabsTrigger>
              <TabsTrigger value="related">Related</TabsTrigger>
              <TabsTrigger value="graph">Graph</TabsTrigger>
            </TabsList>
          </div>

          <TabsContent value="content" className="m-0 p-4">
            <div className="rounded-lg border border-border bg-surface p-4">
              <pre className="overflow-x-auto whitespace-pre-wrap text-xs text-text">{chunk.content}</pre>
            </div>
            <div className="mt-4 flex items-center gap-4 text-xs text-text-muted">
              <span className="flex items-center gap-1">
                <Hash className="h-3 w-3" />
                {chunk.tokens} tokens
              </span>
              <span className="flex items-center gap-1">
                <Clock className="h-3 w-3" />
                {new Date(chunk.createdAt).toLocaleDateString()}
              </span>
            </div>
          </TabsContent>

          <TabsContent value="metadata" className="m-0 p-4">
            <div className="space-y-4">
              <div>
                <h4 className="mb-2 text-xs font-medium uppercase text-text-muted">File Info</h4>
                <div className="space-y-2">
                  <div className="flex items-center justify-between rounded-md border border-border px-3 py-2">
                    <span className="text-xs text-text-muted">File Path</span>
                    <span className="text-xs font-medium text-text">{chunk.filePath}</span>
                  </div>
                  <div className="flex items-center justify-between rounded-md border border-border px-3 py-2">
                    <span className="text-xs text-text-muted">Language</span>
                    <Badge variant="outline">{chunk.language}</Badge>
                  </div>
                  {chunk.framework && (
                    <div className="flex items-center justify-between rounded-md border border-border px-3 py-2">
                      <span className="text-xs text-text-muted">Framework</span>
                      <Badge variant="outline">{chunk.framework}</Badge>
                    </div>
                  )}
                  <div className="flex items-center justify-between rounded-md border border-border px-3 py-2">
                    <span className="text-xs text-text-muted">Repository</span>
                    <span className="text-xs font-medium text-text">{chunk.repository}</span>
                  </div>
                  <div className="flex items-center justify-between rounded-md border border-border px-3 py-2">
                    <span className="text-xs text-text-muted">Collection</span>
                    <span className="text-xs font-medium text-text">{chunk.collection}</span>
                  </div>
                </div>
              </div>

              <div>
                <h4 className="mb-2 text-xs font-medium uppercase text-text-muted">Tags</h4>
                <div className="flex flex-wrap gap-1.5">
                  {chunk.tags.map((tag) => (
                    <Badge key={tag} variant="secondary" className="gap-1 text-[10px]">
                      <Tag className="h-2.5 w-2.5" />
                      {tag}
                    </Badge>
                  ))}
                </div>
              </div>

              <div>
                <h4 className="mb-2 text-xs font-medium uppercase text-text-muted">Similarity</h4>
                <SimilarityBar score={chunk.similarity} />
              </div>
            </div>
          </TabsContent>

          <TabsContent value="related" className="m-0 p-4">
            <div className="space-y-2">
              {chunk.relatedChunks.length === 0 ? (
                <p className="text-sm text-text-muted">No related chunks found</p>
              ) : (
                chunk.relatedChunks.map((relatedId) => (
                  <div
                    key={relatedId}
                    className="flex items-center gap-3 rounded-lg border border-border p-3"
                  >
                    <Link2 className="h-4 w-4 flex-shrink-0 text-text-muted" />
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium text-text">{relatedId}</p>
                      <p className="text-xs text-text-muted">Related chunk</p>
                    </div>
                    <ChevronRight className="h-4 w-4 flex-shrink-0 text-text-muted" />
                  </div>
                ))
              )}
            </div>
          </TabsContent>

          <TabsContent value="graph" className="m-0 p-4">
            <div className="space-y-3">
              <div className="rounded-lg border border-border p-4">
                <div className="mb-3 flex items-center gap-2 text-sm font-medium text-text">
                  <Brain className="h-4 w-4 text-accent" />
                  Relationship Graph
                </div>
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <div className="h-3 w-3 rounded-full bg-accent" />
                    <span className="text-xs text-text">{chunk.id}</span>
                    <span className="text-[10px] text-text-muted">(current)</span>
                  </div>
                  {chunk.relatedChunks.map((relatedId, index) => (
                    <div key={relatedId} className="ml-4 flex items-center gap-2">
                      <div className="flex flex-col items-center">
                        <div className="h-4 w-px bg-border" />
                        <div className="h-2.5 w-2.5 rounded-full bg-surface-hover border border-border" />
                      </div>
                      <span className="text-xs text-text-muted">{relatedId}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="rounded-lg border border-border bg-surface p-3">
                <p className="text-xs text-text-muted">
                  {chunk.relatedChunks.length} related chunks found. Click a related chunk in the
                  &quot;Related&quot; tab to view its details.
                </p>
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}

function CollectionBrowser({ collections, isLoading }: { collections: Collection[]; isLoading: boolean }) {
  if (isLoading) {
    return (
      <div className="space-y-4 p-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <Card key={i}>
            <CardContent className="p-4">
              <Skeleton className="mb-2 h-4 w-40" />
              <Skeleton className="h-3 w-full" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  const totalStorage = collections.reduce((acc, c) => acc + c.storageBytes, 0);

  return (
    <div className="p-4">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-text">Collections</h3>
        <span className="text-xs text-text-muted">
          Total: {formatBytes(totalStorage)} across {collections.length} collections
        </span>
      </div>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {collections.map((collection) => (
          <Card key={collection.id}>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-sm">
                <Database className="h-4 w-4 text-accent" />
                {collection.name}
              </CardTitle>
              <CardDescription>
                {collection.chunkCount.toLocaleString()} chunks · {formatBytes(collection.storageBytes)}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-1.5">
                {collection.repositories.map((repo) => (
                  <div key={repo.name} className="flex items-center justify-between text-xs">
                    <span className="flex items-center gap-1.5 text-text-muted">
                      <FolderOpen className="h-3 w-3" />
                      {repo.name}
                    </span>
                    <span className="font-medium text-text">{repo.count.toLocaleString()}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

export function MemoryExplorer() {
  const [stats, setStats] = useState<MemoryStats>(MOCK_STATS);
  const [collections, setCollections] = useState<Collection[]>(MOCK_COLLECTIONS);
  const [chunks, setChunks] = useState<MemoryChunk[]>(MOCK_CHUNKS);
  const [selectedChunk, setSelectedChunk] = useState<MemoryChunk | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setIsLoading(false), 800);
    return () => clearTimeout(timer);
  }, []);

  const handleRefresh = useCallback(async () => {
    setIsRefreshing(true);
    await new Promise((r) => setTimeout(r, 1200));
    setIsRefreshing(false);
  }, []);

  const handleSelectChunk = useCallback((chunk: MemoryChunk) => {
    setSelectedChunk(chunk);
  }, []);

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <div className="flex items-center justify-between border-b border-border px-6 py-4">
        <div className="flex items-center gap-3">
          <Brain className="h-5 w-5 text-accent" />
          <div>
            <h1 className="text-lg font-semibold text-text">Memory Explorer</h1>
            <p className="text-xs text-text-muted">Semantic memory, knowledge graphs, and embeddings</p>
          </div>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={handleRefresh}
          disabled={isRefreshing}
          leftIcon={isRefreshing ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
        >
          {isRefreshing ? 'Refreshing...' : 'Refresh'}
        </Button>
      </div>

      <div className="flex-1 overflow-y-auto">
        <div className="space-y-6 p-6">
          <StatsOverview stats={stats} isLoading={isLoading} />

          <div className="flex min-h-[500px] gap-0 rounded-lg border border-border overflow-hidden">
            <div className="w-96 flex-shrink-0 border-r border-border">
              <SearchPanel
                chunks={chunks}
                selectedChunk={selectedChunk}
                onSelectChunk={handleSelectChunk}
                isLoading={isLoading}
              />
            </div>
            <div className="flex-1 min-w-0">
              {selectedChunk ? (
                <ChunkViewer chunk={selectedChunk} />
              ) : (
                <div className="flex h-full items-center justify-center text-text-muted">
                  <p>Select a chunk to view details</p>
                </div>
              )}
            </div>
          </div>

          <CollectionBrowser collections={collections} isLoading={isLoading} />
        </div>
      </div>
    </div>
  );
}
