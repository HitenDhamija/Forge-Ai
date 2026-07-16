# Supported Models Reference

## Qwen2.5

Qwen2.5 is Alibaba's latest general-purpose language model, offering strong performance across multiple languages and tasks.

| Variant | Parameters | VRAM (Q4) | VRAM (Q8) | Context | Best For |
|---------|-----------|-----------|-----------|---------|----------|
| `qwen2.5:0.5b` | 500M | 0.5 GB | 0.8 GB | 32K | Edge/embedded devices |
| `qwen2.5:1.5b` | 1.5B | 1.2 GB | 1.8 GB | 32K | Quick responses, mobile |
| `qwen2.5:3b` | 3B | 2.2 GB | 3.4 GB | 32K | Low-resource general chat |
| `qwen2.5:7b` | 7B | 4.4 GB | 7.0 GB | 128K | General purpose, coding |
| `qwen2.5:14b` | 14B | 8.5 GB | 14.0 GB | 128K | Complex reasoning, code |
| `qwen2.5:32b` | 32B | 19.0 GB | 32.0 GB | 128K | High-quality generation |
| `qwen2.5:72b` | 72B | 42.0 GB | 72.0 GB | 128K | Near-frontier quality |

### Strengths
- Excellent multilingual support (30+ languages)
- Strong coding and math capabilities
- Large context window (up to 128K tokens)
- Good instruction following

### Recommended Quantization
- **Q4_K_M**: Best for most use cases (default in ForgeAI)
- **Q8_0**: When quality matters more than speed
- **Q5_K_M**: Middle ground

---

## Llama 3.2

Meta's Llama 3.2 family, optimized for efficiency and edge deployment.

| Variant | Parameters | VRAM (Q4) | VRAM (Q8) | Context | Best For |
|---------|-----------|-----------|-----------|---------|----------|
| `llama3.2:1b` | 1B | 0.8 GB | 1.3 GB | 128K | Ultra-lightweight tasks |
| `llama3.2:3b` | 3B | 2.2 GB | 3.4 GB | 128K | Mobile and edge, chat |
| `llama3.2:8b` | 8B | 5.0 GB | 8.0 GB | 128K | General purpose |
| `llama3.2:90b` | 90B | 52.0 GB | 90.0 GB | 128K | Near-frontier quality |

### Strengths
- Efficient architecture for edge deployment
- Strong instruction following
- Good with structured outputs
- 128K context window

### Recommended Quantization
- **Q4_K_M**: Default recommendation
- **Q4_0**: Smallest footprint for edge devices

---

## Gemma 2

Google's Gemma 2 family, built on Gemini technology.

| Variant | Parameters | VRAM (Q4) | VRAM (Q8) | Context | Best For |
|---------|-----------|-----------|-----------|---------|----------|
| `gemma2:2b` | 2B | 1.6 GB | 2.5 GB | 8K | Lightweight tasks |
| `gemma2:9b` | 9B | 5.5 GB | 9.0 GB | 8K | General purpose, creative |
| `gemma2:27b` | 27B | 16.0 GB | 27.0 GB | 8K | High-quality generation |

### Strengths
- Excellent creative writing
- Strong reasoning capabilities
- Well-balanced personality
- Google's safety training

### Recommended Quantization
- **Q4_K_M**: Default recommendation
- **Q5_K_M**: Better quality for creative tasks

---

## Phi-3

Microsoft's Phi-3 family, designed for efficiency and reasoning.

| Variant | Parameters | VRAM (Q4) | VRAM (Q8) | Context | Best For |
|---------|-----------|-----------|-----------|---------|----------|
| `phi3:mini` | 3.8B | 2.5 GB | 3.8 GB | 128K | Fast reasoning, math |
| `phi3:small` | 7B | 4.4 GB | 7.0 GB | 128K | General purpose |
| `phi3:medium` | 14B | 8.5 GB | 14.0 GB | 128K | Complex analysis |

### Strengths
- Strong mathematical reasoning
- Excellent code understanding
- Efficient architecture
- Long context window (128K)

### Recommended Quantization
- **Q4_K_M**: Default recommendation
- **Q8_0**: For math-heavy tasks

---

## Model Comparison

### Quality vs Speed

```
Quality (approximate)
  │
  │  ████████████████████████████████████████  qwen2.5:72b
  │  ██████████████████████████████████████    llama3.2:90b
  │  ████████████████████████████████          qwen2.5:32b
  │  ██████████████████████████████            gemma2:27b
  │  ████████████████████████████              qwen2.5:14b
  │  ██████████████████████████                phi3:medium
  │  ████████████████████████                  llama3.2:8b
  │  ██████████████████████                    qwen2.5:7b
  │  ████████████████████                      gemma2:9b
  │  ██████████████████                        phi3:small
  │  ████████████████                          llama3.2:3b
  │  ██████████████                            qwen2.5:3b
  │  ████████                                  phi3:mini
  │  ██████                                    qwen2.5:1.5b
  │  ████                                      llama3.2:1b
  │  ██                                        qwen2.5:0.5b
  └──────────────────────────────────────────────────── Speed
```

### Quick Comparison Table

| Model | Quality | Speed | VRAM | Context | Coding | Creative | Reasoning |
|-------|---------|-------|------|---------|--------|----------|-----------|
| qwen2.5:3b | ★★★☆☆ | ★★★★★ | ★★★★★ | ★★★★★ | ★★★☆☆ | ★★★☆☆ | ★★★☆☆ |
| qwen2.5:7b | ★★★★☆ | ★★★★☆ | ★★★★☆ | ★★★★★ | ★★★★☆ | ★★★★☆ | ★★★★☆ |
| qwen2.5:14b | ★★★★★ | ★★★☆☆ | ★★★☆☆ | ★★★★★ | ★★★★★ | ★★★★☆ | ★★★★★ |
| llama3.2:3b | ★★★☆☆ | ★★★★★ | ★★★★★ | ★★★★★ | ★★★☆☆ | ★★★☆☆ | ★★★☆☆ |
| llama3.2:8b | ★★★★☆ | ★★★★☆ | ★★★★☆ | ★★★★★ | ★★★★☆ | ★★★★☆ | ★★★★☆ |
| gemma2:9b | ★★★★☆ | ★★★★☆ | ★★★★☆ | ★★★☆☆ | ★★★★☆ | ★★★★★ | ★★★★☆ |
| phi3:medium | ★★★★☆ | ★★★☆☆ | ★★★☆☆ | ★★★★★ | ★★★★☆ | ★★★☆☆ | ★★★★★ |

---

## Minimum Hardware Requirements

### By Model Size

| Model Size | Min RAM | Min VRAM | Recommended VRAM | Storage |
|-----------|---------|----------|------------------|---------|
| ≤ 2B | 4 GB | 2 GB | 4 GB | 3 GB |
| 3-4B | 8 GB | 4 GB | 6 GB | 5 GB |
| 7-9B | 16 GB | 8 GB | 12 GB | 10 GB |
| 14B | 32 GB | 16 GB | 24 GB | 20 GB |
| 27-32B | 48 GB | 24 GB | 48 GB | 40 GB |
| 70-90B | 96 GB | 48 GB | 80 GB | 80 GB |

### Recommended Configurations

#### Entry Level (~$500)
- **CPU**: AMD Ryzen 5 5600X / Intel i5-12400
- **RAM**: 16 GB DDR4
- **GPU**: RTX 3060 12GB
- **Storage**: 500 GB NVMe SSD
- **Models**: qwen2.5:3b, llama3.2:3b

#### Mid Range (~$1,200)
- **CPU**: AMD Ryzen 7 5800X3D / Intel i7-13700K
- **RAM**: 32 GB DDR4/DDR5
- **GPU**: RTX 3090 24GB
- **Storage**: 1 TB NVMe SSD
- **Models**: qwen2.5:7b, llama3.2:8b, gemma2:9b

#### High End (~$2,500)
- **CPU**: AMD Ryzen 9 7950X / Intel i9-14900K
- **RAM**: 64 GB DDR5
- **GPU**: RTX 4090 24GB
- **Storage**: 2 TB NVMe SSD
- **Models**: qwen2.5:14b, phi3:medium

#### Professional (~$5,000+)
- **CPU**: AMD Threadripper / Intel Xeon
- **RAM**: 128 GB ECC
- **GPU**: 2x RTX 4090 or A100 80GB
- **Storage**: 4 TB NVMe RAID
- **Models**: qwen2.5:32b, qwen2.5:72b (multi-GPU)

---

## Model Selection Guide

### Choose based on your use case:

| If you need... | Use this model |
|----------------|----------------|
| Fastest possible responses | qwen2.5:0.5b or llama3.2:1b |
| Best quality under 4GB VRAM | qwen2.5:3b |
| Balanced quality and speed | qwen2.5:7b |
| Best coding assistance | qwen2.5:14b |
| Best creative writing | gemma2:9b |
| Best math/reasoning | phi3:medium |
| Best overall quality | qwen2.5:32b or qwen2.5:72b |
| Mobile/edge deployment | llama3.2:1b or llama3.2:3b |
