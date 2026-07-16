# ForgeAI

**The Complete AI Engineering Platform**

ForgeAI is an enterprise-grade AI engineering platform that transforms how teams build, analyze, and evolve software. It combines repository intelligence, semantic memory, knowledge graphs, and AI agents into a unified platform.

## Features

- **Repository Intelligence** - Deep code analysis with AI
- **Semantic Memory** - Context-aware knowledge retrieval
- **Knowledge Graph** - Visual relationship mapping
- **AI Agents** - Specialized engineering assistants
- **Workflow Automation** - Visual workflow builder
- **Learning Engine** - Continuous improvement system
- **Monitoring** - Real-time platform observability
- **Studio** - Visual AI engineering environment
- **Organizations** - Multi-repository collaboration
- **Plugin System** - Extensible architecture

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+
- Ollama (for local AI)

### Installation
```bash
# Clone the repository
git clone https://github.com/forgeai/forgeai.git
cd forgeai

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt

# Frontend setup
cd ../frontend
npm install

# Start services
docker-compose up -d  # Start PostgreSQL and Redis
cd ../backend
uvicorn app.main:app --reload

# In another terminal
cd ../frontend
npm run dev
```

### Access
- Frontend: http://localhost:3000
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Architecture

ForgeAI follows a modular, microservices-inspired architecture:

- **Backend**: Python/FastAPI with async support
- **Frontend**: Next.js 15 with React 19
- **Database**: PostgreSQL with SQLAlchemy 2.0
- **Cache**: Redis for caching and sessions
- **AI**: Ollama for local model inference

## Documentation

- [Architecture Overview](./ARCHITECTURE.md)
- [Developer Guide](./DEVELOPER_GUIDE.md)
- [API Reference](./API_REFERENCE.md)
- [Deployment Guide](./DEPLOYMENT.md)
- [Troubleshooting](./TROUBLESHOOTING.md)

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](./LICENSE)

## Support

- Documentation: https://docs.forgeai.dev
- Issues: https://github.com/forgeai/forgeai/issues
- Discord: https://discord.gg/forgeai
