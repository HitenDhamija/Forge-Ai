# ForgeAI AI Module Architecture

## Overview

The ForgeAI AI module provides a pluggable interface for interacting with local and remote LLMs. It is built around [Ollama](https://ollama.com) as the primary inference backend, supporting fully local model execution with GPU acceleration. The module is designed to be provider-agnostic, allowing future integration with OpenAI, Anthropic, and other backends.

## Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      API Layer (FastAPI)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Chat Router  │  │ Model Router │  │ Health Route │      │
│  └──────┬───────┘  └──────┬───────┘  └──────────────┘      │
└─────────┼──────────────────┼────────────────────────────────┘
          │                  │
          ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                    Service Layer                              │
│  ┌──────────────────┐  ┌──────────────────┐                 │
│  │ ChatController   │  │ ModelManager     │                 │
│  │ (orchestrates    │  │ (list, switch,   │                 │
│  │  chat flow)      │  │  pull, delete)   │                 │
│  └────────┬─────────┘  └────────┬─────────┘                 │
│           │                     │                            │
│  ┌────────▼─────────┐  ┌────────▼─────────┐                 │
│  │ PromptRegistry   │  │ ConversationMgr  │                 │
│  │ (system prompts, │  │ (history, memory │                 │
│  │  templates)      │  │  management)     │                 │
│  └────────┬─────────┘  └────────┬─────────┘                 │
└───────────┼─────────────────────┼────────────────────────────┘
            │                     │
            ▼                     ▼
┌─────────────────────────────────────────────────────────────┐
│                   Client Layer                                │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                  OllamaClient                        │   │
│  │  - health_check()    - list_models()                 │   │
│  │  - generate()        - show_model()                  │   │
│  │  - generate_stream() - pull_model()                  │   │
│  │  - close()           - delete_model()                │   │
│  └──────────────────────────┬───────────────────────────┘   │
└─────────────────────────────┼────────────────────────────────┘
                              │  HTTP (httpx)
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Ollama Server                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │  Model   │  │  Model   │  │  Model   │                  │
│  │ qwen2.5  │  │ llama3.2 │  │  gemma   │                  │
│  └──────────┘  └──────────┘  └──────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow for Chat Requests

```
1. Client sends POST /api/v1/chat with ChatRequest
        │
2. ChatController validates input via PromptRegistry
        │
3. ConversationManager loads/creates conversation history
        │
4. System prompt is prepended from PromptRegistry
        │
5. OllamaClient.generate_stream() sends to Ollama
        │
6. Streaming chunks are yielded as ChatStreamChunk
        │
7. ConversationManager persists messages
        │
8. Client receives SSE stream with token-by-token output
```

## Streaming Architecture

The streaming system uses Server-Sent Events (SSE) to deliver token-by-token responses:

1. **Request Validation**: `ChatRequest` is validated (message length, model name).
2. **Conversation History**: Messages are loaded or a new conversation is created.
3. **Prompt Assembly**: System prompt + history + user message are assembled.
4. **Ollama Streaming**: `OllamaClient.generate_stream()` yields `ChatStreamChunk` objects.
5. **SSE Encoding**: Each chunk is encoded as an SSE event and sent to the client.
6. **Final Chunk**: A `done=True` chunk signals the end of the stream.

### Key Files

- `app/ai/clients/ollama.py` — `generate_stream()` method handles NDJSON line parsing.
- `app/ai/schemas/chat.py` — `ChatStreamChunk` schema for wire format.

## Memory System Design

The conversation memory system manages message history within and across conversations:

- **In-Memory Buffer**: Recent messages are kept in a list, bounded by `CONVERSATION_MAX_MESSAGES`.
- **Context Window**: Only the last N messages are sent to the model, respecting `MAX_CONTEXT_LENGTH`.
- **Message Persistence**: Full conversation history is stored (database-backed in production).
- **Memory Pruning**: Older messages are summarized or truncated when the context window is exceeded.

### Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `CONVERSATION_MAX_MESSAGES` | 100 | Max messages per conversation |
| `CONVERSATION_MEMORY_ENABLED` | True | Enable/disable memory system |
| `MAX_CONTEXT_LENGTH` | 4096 | Maximum context tokens for the model |

## Prompt Engine Design

The prompt engine manages system prompts and templates:

- **PromptRegistry**: Stores named system prompts that can be referenced by ID.
- **Template Variables**: Prompts support `{{variable}}` substitution.
- **Validation**: Prompts are validated against length limits before sending.
- **Versioning**: Prompt versions allow A/B testing of different system prompts.

## Model Management

The `ModelManager` provides a high-level interface for model operations:

```python
# List available models
models = await model_manager.list_models()

# Switch the active model
await model_manager.switch_model("llama3.2:3b")

# Get model details
info = await model_manager.get_model_info("qwen2.5")

# Pull a new model
await model_manager.pull_model("gemma2:9b")
```

### Model Status Lifecycle

```
offline → loading → loaded → running → (unloaded) → available
```

## Error Handling Strategy

All AI exceptions inherit from `ForgeBaseException` and are mapped to HTTP responses:

| Exception | HTTP Status | Description |
|-----------|-------------|-------------|
| `OllamaConnectionException` | 503 | Cannot reach Ollama server |
| `ModelNotFoundException` | 404 | Requested model not installed |
| `ModelLoadingException` | 500 | Model failed to load |
| `PromptTooLongException` | 400 | Input exceeds context window |
| `ConversationNotFoundException` | 404 | Conversation does not exist |
| `ModelSwitchException` | 500 | Failed to switch active model |
| `AITimeoutException` | 504 | Request timed out |
| `StreamingException` | 500 | Error during stream generation |

### Retry Strategy

The `OllamaClient` uses `tenacity` for automatic retries:
- **3 attempts** for connection errors (`ConnectError`, `ConnectTimeout`).
- **Exponential backoff**: 0.5s → 1s → 2s (capped at 4s).
- No retries for model-not-found or prompt-too-long errors.

## Extension Points

### LangGraph Integration

The module is designed to support LangGraph for agentic workflows:
- Define graph nodes that wrap Ollama calls.
- Use conversation state as the graph state.
- Support branching logic for multi-turn agent interactions.

### MCP (Model Context Protocol)

Future support for MCP would enable:
- Tool-use patterns where the model can call external functions.
- Structured output parsing from model responses.
- Function-calling schemas registered per-model.

### RAG (Retrieval-Augmented Generation)

The prompt engine supports injecting context from external sources:
- Add retrieved documents to the system prompt.
- Support for vector store integration (pgvector, ChromaDB).
- Chunking and embedding pipeline for document ingestion.

### Agent Framework

The controller pattern supports multi-agent architectures:
- **Orchestrator Agent**: Routes tasks to specialized agents.
- **Tool Agent**: Has access to external tools (web search, code execution).
- **Critic Agent**: Evaluates responses for quality and safety.

## Security Considerations

1. **Network Isolation**: Ollama runs on a private Docker network (`forge-network`). Only the backend container can reach it.
2. **No External Exposure**: In production, Ollama's port (11434) is not published to the host.
3. **Input Validation**: All prompts are validated for length and content before being sent to the model.
4. **Secrets Management**: API keys (if using cloud providers) are stored in environment variables, never in code.
5. **Rate Limiting**: Chat endpoints are rate-limited per user to prevent abuse.
6. **Output Filtering**: Model outputs can be post-processed for sensitive content (extensible).
7. **GPU Access Control**: Docker `device reservations` ensure only authorized containers access GPU hardware.
