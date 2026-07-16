# Ollama Setup Guide

## What is Ollama?

[Ollama](https://ollama.com) is a lightweight runtime for running large language models (LLMs) locally. It provides a simple API for model management and inference, supporting a wide range of open-source models including Qwen, Llama, Gemma, and Phi.

### Key Features

- **Local inference**: Run models on your own hardware with no data leaving your machine.
- **GPU acceleration**: Automatic CUDA/Metal/ROCm support for faster inference.
- **Model library**: Pull pre-quantized models from the Ollama registry.
- **Simple API**: REST API compatible with OpenAI's format.
- **Docker support**: Official Docker images with GPU passthrough.

## Installation

### macOS

```bash
# Download from https://ollama.com/download/mac
# Or install via Homebrew:
brew install ollama
```

### Linux

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### Windows

Download the installer from https://ollama.com/download/windows and run the `.exe` file.

### Verify Installation

```bash
ollama --version
```

## Starting the Ollama Service

### Standalone (macOS/Linux)

```bash
# Start the Ollama server
ollama serve

# The server listens on http://localhost:11434 by default
```

### As a System Service (Linux)

```bash
# Ollama installs a systemd service automatically
sudo systemctl start ollama
sudo systemctl enable ollama

# Check status
sudo systemctl status ollama

# View logs
journalctl -u ollama -f
```

### Verifying the Service

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# List installed models
ollama list

# Check server version
curl http://localhost:11434/api/version
```

## Pulling Your First Model

```bash
# Pull a model (downloads ~2GB for 3B parameter models)
ollama pull qwen2.5

# Run an interactive chat
ollama run qwen2.5

# Pull a specific size variant
ollama pull qwen2.5:3b
ollama pull qwen2.5:7b
ollama pull qwen2.5:14b
```

## Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_HOST` | `0.0.0.0:11434` | Address to bind the server |
| `OLLAMA_MODELS` | `~/.ollama/models` | Model storage directory |
| `OLLAMA_NUM_PARALLEL` | `1` | Number of parallel requests |
| `OLLAMA_MAX_LOADED_MODELS` | `1` | Max models kept in memory |
| `OLLAMA_GPU_LAYERS` | `-1` | GPU layers (auto) |

### Server Configuration

```bash
# Bind to a specific address
OLLAMA_HOST=127.0.0.1:11434 ollama serve

# Allow parallel requests
OLLAMA_NUM_PARALLEL=4 ollama serve

# Store models in a custom location
OLLAMA_MODELS=/data/ollama/models ollama serve
```

## Docker Setup with GPU Support

### Basic Docker

```bash
docker run -d \
  --name ollama \
  -p 11434:11434 \
  -v ollama_data:/root/.ollama \
  ollama/ollama:latest
```

### Docker with NVIDIA GPU

```bash
# Prerequisites: Install nvidia-container-toolkit
# https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html

docker run -d \
  --name ollama \
  --gpus all \
  -p 11434:11434 \
  -v ollama_data:/root/.ollama \
  ollama/ollama:latest
```

### Docker Compose (ForgeAI)

The ForgeAI project includes Ollama in both development and production Docker Compose files:

```bash
# Development
cd docker
docker compose -f docker-compose.dev.yml up ollama

# Production
cd docker
docker compose up ollama
```

### Verifying GPU Access in Docker

```bash
# Run nvidia-smi inside the container
docker exec -it forgeai-ollama nvidia-smi

# Check Ollama is using GPU
curl http://localhost:11434/api/ps
```

## Troubleshooting

### Ollama Won't Start

```bash
# Check if port 11434 is in use
lsof -i :11434

# Check logs
journalctl -u ollama -n 50

# Try starting manually
ollama serve
```

### Model Download Fails

```bash
# Check internet connection
curl -I https://ollama.com

# Check disk space
df -h

# Clear cache and retry
rm -rf ~/.ollama/models/manifests
ollama pull qwen2.5
```

### GPU Not Detected

```bash
# Verify NVIDIA driver
nvidia-smi

# Check CUDA version
nvcc --version

# In Docker, verify nvidia-container-toolkit
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi
```

### Slow Performance

```bash
# Check GPU utilization
nvidia-smi

# Reduce context length in ForgeAI config
# AI_MAX_CONTEXT_LENGTH=2048

# Use a smaller model variant
ollama pull qwen2.5:3b
```

### Out of Memory (OOM)

```bash
# Check available VRAM
nvidia-smi

# Use a smaller quantization
ollama pull qwen2.5:1.5b

# Reduce parallel requests
OLLAMA_NUM_PARALLEL=1 ollama serve
```

## Next Steps

- [Running Local Models](Running-Local-Models.md) — Guide to model selection and optimization.
- [Supported Models](Supported-Models.md) — Full reference of supported models and requirements.
