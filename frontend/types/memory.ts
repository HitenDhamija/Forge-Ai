export type ChunkType =
  | "repository"
  | "module"
  | "class"
  | "function"
  | "route"
  | "database"
  | "config"
  | "documentation";

export interface SemanticChunk {
  id: string;
  repository_id: string;
  chunk_type: ChunkType;
  content: string;
  metadata: Record<string, any>;
  embedding_model: string | null;
  version: number;
  created_at: string;
}

export interface SearchResult {
  chunk: SemanticChunk;
  score: number;
  rank: number;
  explanation: string | null;
}

export interface SearchRequest {
  query: string;
  repository_id?: string;
  chunk_types?: ChunkType[];
  language?: string;
  framework?: string;
  tags?: string[];
  top_k?: number;
  similarity_threshold?: number;
}

export interface SearchResponse {
  query: string;
  results: SearchResult[];
  total_results: number;
  search_time_ms: number;
  query_classification: string | null;
}

export interface ContextRequest {
  query: string;
  repository_id?: string;
  max_tokens?: number;
}

export interface ContextResponse {
  query: string;
  context: string;
  chunks_used: SearchResult[];
  query_classification: string;
  token_count: number;
  build_time_ms: number;
}

export interface IndexRequest {
  repository_id: string;
  repository_name: string;
  force_reindex?: boolean;
}

export interface IndexResponse {
  repository_id: string;
  chunks_indexed: number;
  collections_updated: string[];
  index_time_ms: number;
}

export interface CollectionStats {
  name: string;
  count: number;
  size_bytes: number | null;
  last_updated: string | null;
}

export interface MemoryStats {
  total_chunks: number;
  total_repositories: number;
  collections: CollectionStats[];
  embedding_model: string;
  embedding_dimension: number;
  storage_size_bytes: number | null;
}

export interface IndexedRepository {
  id: string;
  name: string;
  chunks_count?: number;
}
