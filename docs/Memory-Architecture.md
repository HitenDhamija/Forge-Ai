# Semantic Memory Engine Architecture

## Overview

The ForgeAI Semantic Memory Engine provides long-term, context-aware memory capabilities for AI agents. It enables semantic search, context retrieval, and knowledge persistence across conversations and sessions.

## Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Semantic Memory Engine                     │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  Embedding   │  │   Vector    │  │  Semantic   │        │
│  │   Service    │  │    Store    │  │  Chunker    │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│         │                │                │                  │
│         ▼                ▼                ▼                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Retrieval & Reranking                   │   │
│  └─────────────────────────────────────────────────────┘   │
│         │                                                    │
│         ▼                                                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Context   │  │    Query    │  │ Relationship│        │
│  │   Builder   │  │ Classifier  │  │    Graph    │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Embedding Service

**Purpose**: Converts text into dense vector representations for semantic comparison.

**Implementation**:
- Primary model: `BAAI/bge-small-en-v1.5` (512 dimensions)
- Fallback model: `all-MiniLM-L6-v2` (384 dimensions)
- Uses `sentence-transformers` library with async wrapper

**Key Features**:
- Batch embedding support for efficiency
- Automatic model fallback on errors
- Embedding caching for repeated queries
- Dimension normalization for cross-model compatibility

**Configuration**:
```python
class EmbeddingConfig:
    model_name: str = "BAAI/bge-small-en-v1.5"
    fallback_model: str = "all-MiniLM-L6-v2"
    batch_size: int = 32
    max_retries: int = 3
    device: str = "auto"  # auto, cpu, cuda
```

### 2. Vector Store (ChromaDB)

**Purpose**: Stores and retrieves vector embeddings with metadata.

**Implementation**:
- ChromaDB client with persistent storage
- Collections for different memory types (conversation, knowledge, code)
- Metadata filtering support

**Collection Schema**:
```python
{
    "id": "uuid",
    "embedding": "float[]",
    "document": "text content",
    "metadata": {
        "source": "conversation|code|documentation",
        "timestamp": "ISO8601",
        "session_id": "uuid",
        "importance": "float 0-1",
        "tags": ["list", "of", "strings"],
        "relationships": ["connected", "memory", "ids"]
    }
}
```

**Configuration**:
```python
class VectorStoreConfig:
    host: str = "chromadb"
    port: int = 8000
    collection_prefix: str = "forgeai"
    persist_directory: str = "/chroma/chroma"
```

### 3. Semantic Chunker

**Purpose**: Splits documents into semantically meaningful chunks while preserving context.

**Strategy**:
1. **Paragraph Detection**: Split on paragraph boundaries
2. **Semantic Similarity**: Merge similar consecutive chunks
3. **Token Limit Enforcement**: Split oversized chunks at natural boundaries
4. **Overlap Management**: Maintain context window between chunks

**Chunking Algorithm**:
```python
def chunk_document(text: str, max_tokens: int = 512) -> List[Chunk]:
    # Step 1: Split into paragraphs
    paragraphs = split_paragraphs(text)
    
    # Step 2: Merge semantically similar paragraphs
    merged = merge_similar_chunks(paragraphs, threshold=0.7)
    
    # Step 3: Enforce token limits
    final_chunks = enforce_token_limit(merged, max_tokens)
    
    # Step 4: Add overlap for context
    return add_overlap(final_chunks, overlap_tokens=50)
```

**Chunk Metadata**:
- Start/end positions in original text
- Heading hierarchy (if applicable)
- Semantic type (code, text, list, etc.)
- Importance score

### 4. Hybrid Retrieval System

**Purpose**: Combines multiple retrieval strategies for optimal results.

**Retrieval Pipeline**:

```
Query → [Dense Retrieval] → [Sparse Retrieval] → [Metadata Filter] → Results
              ↓                    ↓                      ↓
         Vector Search        BM25/TF-IDF          Tag/Source Filter
```

**Dense Retrieval**:
- Cosine similarity search
- Approximate nearest neighbor (ANN) via ChromaDB
- Configurable top-k results

**Sparse Retrieval**:
- BM25-based keyword matching
- TF-IDF scoring
- Term frequency normalization

**Result Fusion**:
```python
def hybrid_search(query: str, top_k: int = 20) -> List[Memory]:
    dense_results = vector_store.search(query, top_k=top_k * 2)
    sparse_results = bm25_index.search(query, top_k=top_k * 2)
    
    # Reciprocal Rank Fusion
    fused_scores = reciprocal_rank_fusion(
        dense_results, 
        sparse_results, 
        k=60
    )
    
    return sorted(fused_scores, key=lambda x: x.score, reverse=True)[:top_k]
```

### 5. Reranking Algorithm

**Purpose**: Refines search results for maximum relevance.

**Multi-Stage Reranking**:

1. **Initial Scoring**: Combine dense + sparse scores
2. **Freshness Boost**: Prioritize recent memories
3. **Importance Weighting**: Factor in memory importance scores
4. **Diversity Enforcement**: Ensure varied results
5. **Context Coherence**: Group related memories

**Reranking Formula**:
```
final_score = (
    0.4 * semantic_score +
    0.3 * keyword_score +
    0.15 * recency_score +
    0.1 * importance_score +
    0.05 * diversity_bonus
)
```

### 6. Context Builder

**Purpose**: Assembles retrieved memories into optimal context for LLM consumption.

**Context Assembly**:
```python
def build_context(
    query: str,
    memories: List[Memory],
    max_tokens: int = 4096
) -> Context:
    # Step 1: Rank by relevance
    ranked = rank_by_relevance(memories, query)
    
    # Step 2: Group by topic
    grouped = group_by_topic(ranked)
    
    # Step 3: Select diverse set
    selected = select_diverse(grouped, max_tokens)
    
    # Step 4: Format for LLM
    return format_context(selected, query)
```

**Context Format**:
```
[Relevant Memories]

Topic: {topic_name}
- Memory 1: {content} (importance: 0.9, age: 2 days)
- Memory 2: {content} (importance: 0.7, age: 1 week)

Topic: {another_topic}
- Memory 3: {content} (importance: 0.8, age: 3 days)

[Summary]
Based on {n} relevant memories spanning {timeframe}.
```

### 7. Query Classifier

**Purpose**: Categorizes queries to optimize retrieval strategy.

**Classification Categories**:
- **Factual**: Specific information requests
- **Conceptual**: Understanding/explanation requests
- **Procedural**: How-to questions
- **Contextual**: Conversation history dependent
- **Exploratory**: Open-ended discovery

**Classification Logic**:
```python
def classify_query(query: str) -> QueryType:
    # Pattern matching
    if contains_question_words(query):
        return QueryType.FACTUAL
    
    if contains_explanation_patterns(query):
        return QueryType.CONCEPTUAL
    
    if contains_how_to_patterns(query):
        return QueryType.PROCEDURAL
    
    # Semantic classification via embedding similarity
    embedding = embed_query(query)
    return classify_by_embedding(embedding)
```

**Strategy Adaptation**:
| Query Type | Retrieval Strategy | Reranking | Context Style |
|------------|-------------------|-----------|---------------|
| Factual | Precision-focused | High | Concise |
| Conceptual | Breadth-focused | Medium | Comprehensive |
| Procedural | Step-focused | High | Sequential |
| Contextual | Temporal-focused | Low | Chronological |
| Exploratory | Diversity-focused | Low | Varied |

### 8. Relationship Graph

**Purpose**: Maintains connections between memories for graph-based retrieval.

**Graph Structure**:
```
Memory A ──[related_to]──▶ Memory B
    │                          │
    └──[caused_by]──▶ Memory C ◀──[triggers]── Memory D
```

**Relationship Types**:
- `related_to`: Semantic similarity
- `caused_by`: Causal relationship
- `triggers`: Temporal/sequential
- `contradicts`: Conflicting information
- `supports`: Supporting evidence
- `elaborates`: More detail on topic

**Graph Operations**:
```python
def find_related(memories: List[Memory], depth: int = 2) -> Graph:
    graph = build_relationship_graph(memories)
    return graph.bfs(start_nodes=memories, max_depth=depth)
```

## API Endpoints

### Memory Management
- `POST /api/v1/memory/index` - Index new memories
- `DELETE /api/v1/memory/{id}` - Remove memory
- `GET /api/v1/memory/{id}` - Retrieve specific memory
- `PUT /api/v1/memory/{id}` - Update memory metadata

### Search & Retrieval
- `POST /api/v1/memory/search` - Semantic search
- `POST /api/v1/memory/context` - Get context for query
- `POST /api/v1/memory/related` - Find related memories

### Administration
- `GET /api/v1/memory/stats` - Collection statistics
- `POST /api/v1/memory/reindex` - Reindex collection
- `DELETE /api/v1/memory/collection/{name}` - Delete collection

## Data Flow

### Indexing Flow
```
User Input → Chunking → Embedding → Vector Store → Relationship Graph
                    ↓
              Metadata Extraction
                    ↓
              Storage (PostgreSQL)
```

### Retrieval Flow
```
Query → Classification → Strategy Selection → Hybrid Search → Reranking → Context Building → Response
                              ↓
                    Metadata Filtering
```

## Performance Considerations

### Optimization Strategies

1. **Embedding Caching**
   - Cache frequently accessed embeddings
   - LRU eviction policy
   - Reduces model inference calls

2. **Batch Processing**
   - Batch embedding operations
   - Parallel vector operations
   - Asynchronous metadata updates

3. **Index Optimization**
   - Periodic index maintenance
   - HNSW index tuning
   - Compression for large collections

4. **Query Optimization**
   - Query result caching
   - Predictive pre-fetching
   - Lazy loading of relationships

### Scalability

**Horizontal Scaling**:
- ChromaDB cluster mode
- Read replicas for search
- Sharding by collection

**Vertical Scaling**:
- GPU acceleration for embeddings
- Increased memory for caching
- SSD storage for vectors

### Monitoring

**Key Metrics**:
- Embedding latency (p50, p95, p99)
- Search latency
- Index size and growth rate
- Cache hit ratio
- Memory freshness distribution

**Alerting Thresholds**:
- Embedding latency > 100ms
- Search latency > 500ms
- Cache hit ratio < 80%
- Index size > 10GB

## Security

### Access Control
- Collection-level permissions
- User-scoped memory access
- API key authentication

### Data Protection
- Encryption at rest (ChromaDB)
- Encryption in transit (TLS)
- PII detection and redaction
- Audit logging

## Future Enhancements

### Short-term (Q1-Q2)
- [ ] Multi-modal embeddings (text + images)
- [ ] Real-time streaming updates
- [ ] Advanced relationship inference
- [ ] Memory consolidation algorithms

### Medium-term (Q3-Q4)
- [ ] Distributed graph database
- [ ] Federated memory across instances
- [ ] Adaptive chunking based on content type
- [ ] Cross-lingual memory support

### Long-term (Year 2)
- [ ] Neural memory architecture
- [ ] Self-organizing memory clusters
- [ ] Predictive memory retrieval
- [ ] Memory pruning and archival strategies
