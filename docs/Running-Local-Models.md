# Running Local Models with ForgeAI

## How to Pull Models

Ollama manages models through its registry. Use the CLI or API to download models:

```bash
# Pull by name (defaults to latest size)
ollama pull qwen2.5

# Pull a specific size variant
ollama pull qwen2.5:3b
ollama pull qwen2.5:7b
ollama pull qwen2.5:14b
ollama pull qwen2.5:32b

# Pull a model with specific quantization
ollama pull qwen2.5:7b-instruct-q4_K_M

# List all installed models
ollama list

# Check model details
ollama show qwen2.5

# Remove a model
ollama rm qwen2.5:3b
```

### Pulling via the API

```bash
# Start a pull (streaming progress)
curl -s http://localhost:11434/api/pull \
  -d '{"name": "qwen2.5", "stream": true}'
```

## Recommended Models by Use Case

### General Purpose Chat

| Model | Size | Best For |
|-------|------|----------|
| `qwen2.5:3b` | 3B | Fast responses, low resource usage |
| `qwen2.5:7b` | 7B | Balanced quality and speed |
| `qwen2.5:14b` | 14B | High quality, needs more VRAM |
| `llama3.2:3b` | 3B | Meta's latest, excellent instruction following |
| `llama3.2:8b` | 8B | Strong general performance |

### Coding Assistance

| Model | Size | Best For |
|-------|------|----------|
| `qwen2.5:7b` | 7B | Code generation and explanation |
| `qwen2.5:14b` | 14B | Complex code tasks |
| `codellama:7b` | 7B | Code-specific fine-tune |
| `codellama:13b` | 13B | Advanced code generation |

### Creative Writing

| Model | Size | Best For |
|-------|------|----------|
| `llama3.2:8b` | 8B | Creative and narrative tasks |
| `gemma2:9b` | 9B | Google's creative model |
| `phi3:14b` | 14B | Microsoft's capable small model |

### Analysis & Reasoning

| Model | Size | Best For |
|-------|------|----------|
| `qwen2.5:14b` | 14B | Complex reasoning tasks |
| `qwen2.5:32b` | 32B | Highest quality reasoning |
| `gemma2:27b` | 27B | Deep analysis |

## Model Sizes and Hardware Requirements

### VRAM Requirements (Approximate)

| Model Size | Q4_K_M | Q8_0 | FP16 |
|-----------|--------|------|------|
| 1.5B | 1.2 GB | 1.8 GB | 3.0 GB |
| 3B | 2.2 GB | 3.4 GB | 6.0 GB |
| 7B | 4.4 GB | 7.0 GB | 14.0 GB |
| 14B | 8.5 GB | 14.0 GB | 28.0 GB |
| 32B | 19.0 GB | 32.0 GB | 64.0 GB |

### Minimum Hardware

| Use Case | RAM | VRAM | Storage |
|----------|-----|------|---------|
| 3B model (Q4) | 8 GB | 4 GB | 5 GB |
| 7B model (Q4) | 16 GB | 8 GB | 10 GB |
| 14B model (Q4) | 32 GB | 16 GB | 20 GB |
| 32B model (Q4) | 64 GB | 24 GB | 40 GB |

### Recommended Hardware

| Tier | CPU | RAM | GPU | Storage |
|------|-----|-----|-----|---------|
| **Budget** | 4 cores | 16 GB | RTX 3060 12GB | 50 GB SSD |
| **Mid-range** | 8 cores | 32 GB | RTX 3090 24GB | 100 GB SSD |
| **High-end** | 16 cores | 64 GB | RTX 4090 24GB | 200 GB NVMe |

## GPU vs CPU Inference

### GPU Inference

- **Speed**: 10-50x faster than CPU for large models.
- **VRAM Limit**: Model must fit in GPU memory.
- **Multi-GPU**: Ollama supports model parallelism across GPUs.

```bash
# Force GPU usage (default if available)
ollama run qwen2.5

# Check GPU utilization
nvidia-smi
```

### CPU Inference

- **Slower**: Expect 5-20 tokens/second for 7B models.
- **No VRAM Limit**: Use system RAM instead.
- **Quantization**: Q4_K_M recommended for CPU to reduce memory usage.

```bash
# CPU-only inference (set GPU_LAYERS=0)
OLLAMA_GPU_LAYERS=0 ollama serve
```

### Hybrid (Partial GPU Offload)

Ollama automatically splits layers between GPU and CPU when VRAM is insufficient:

```bash
# Auto-detect split
ollama run qwen2.5:14b
# Uses GPU for first N layers, CPU for the rest
```

## Performance Optimization

### 1. Use Appropriate Quantization

```bash
# Q4_K_M — Best balance of quality and speed (recommended)
ollama pull qwen2.5:7b-instruct-q4_K_M

# Q8_0 — Higher quality, more VRAM
ollama pull qwen2.5:7b-instruct-q8_0

# Q5_K_M — Middle ground
ollama pull qwen2.5:7b-instruct-q5_K_M
```

### 2. Tune Context Length

```bash
# In ForgeAI, set via environment variable
AI_MAX_CONTEXT_LENGTH=4096   # Default
AI_MAX_CONTEXT_LENGTH=2048   # Faster, less context
AI_MAX_CONTEXT_LENGTH=8192   # More context, more VRAM
```

### 3. Control Parallelism

```bash
# Only one request at a time (lowest latency)
OLLAMA_NUM_PARALLEL=1 ollama serve

# Handle 4 concurrent requests (more VRAM needed)
OLLAMA_NUM_PARALLEL=4 ollama serve
```

### 4. Keep Models Loaded

```bash
# Keep multiple models in memory
OLLAMA_MAX_LOADED_MODELS=3 ollama serve
```

### 5. Temperature Tuning

```bash
# Lower temperature for factual/precise tasks
AI_TEMPERATURE=0.3

# Higher temperature for creative tasks
AI_TEMPERATURE=0.9
```

## Switching Models

### Via Ollama CLI

```bash
# Run a different model
ollama run llama3.2

# Switch back
ollama run qwen2.5
```

### Via ForgeAI API

```bash
# Switch the active model
curl -X POST http://localhost:8000/api/v1/ai/models/switch \
  -H "Content-Type: application/json" \
  -d '{"model_name": "llama3.2:3b"}'

# Or specify per-request
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "model": "llama3.2:3b"}'
```

### Listing Available Models

```bash
# Via Ollama
ollama list

# Via ForgeAI API
curl http://localhost:8000/api/v1/ai/models
```

## Model Updates

```bash
# Update a model to latest version
ollama pull qwen2.5

# Check for updates
ollama list  # Compare modified_at dates
```
