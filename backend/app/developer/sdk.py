"""SDK definitions and documentation."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class SDKLanguage(Enum):
    PYTHON = "python"
    TYPESCRIPT = "typescript"
    REST = "rest"


@dataclass
class SDKMethod:
    name: str
    description: str
    parameters: list[dict[str, Any]]
    returns: str
    example: str


@dataclass
class SDKClient:
    language: SDKLanguage
    version: str
    base_url: str
    auth_method: str
    methods: list[SDKMethod] = field(default_factory=list)


class SDKDocumentation:
    def __init__(self) -> None:
        self._methods: dict[str, dict[SDKLanguage, SDKMethod]] = {}
        self._examples: dict[str, dict[SDKLanguage, list[str]]] = {}
        self._init_methods()
        self._init_examples()

    def _init_methods(self) -> None:
        defs = {
            "authenticate": {
                "description": "Authenticate with the ForgeAI API and obtain an access token",
                "parameters": [{"name": "api_key", "type": "string", "required": True, "description": "Your API key"}],
                "returns": "AccessToken",
                "python": "client.authenticate(api_key='your-api-key')",
                "typescript": "client.authenticate({ apiKey: 'your-api-key' })",
                "rest": "POST /api/v1/auth/token\nBody: { \"api_key\": \"your-api-key\" }",
            },
            "list_repositories": {
                "description": "List all repositories accessible to the authenticated user",
                "parameters": [{"name": "page", "type": "integer", "required": False, "description": "Page number"}, {"name": "per_page", "type": "integer", "required": False, "description": "Results per page"}],
                "returns": "list[Repository]",
                "python": "repos = client.list_repositories(page=1, per_page=20)",
                "typescript": "const repos = client.listRepositories({ page: 1, perPage: 20 })",
                "rest": "GET /api/v1/repositories?page=1&per_page=20",
            },
            "get_repository": {
                "description": "Get detailed information about a specific repository",
                "parameters": [{"name": "repo_id", "type": "string", "required": True, "description": "Repository ID"}],
                "returns": "Repository",
                "python": "repo = client.get_repository(repo_id='repo-123')",
                "typescript": "const repo = client.getRepository({ repoId: 'repo-123' })",
                "rest": "GET /api/v1/repositories/{repo_id}",
            },
            "analyze_repository": {
                "description": "Run AI analysis on a repository's codebase",
                "parameters": [{"name": "repo_id", "type": "string", "required": True, "description": "Repository ID"}, {"name": "analysis_type", "type": "string", "required": False, "description": "Type of analysis (quality, security, performance)"}],
                "returns": "AnalysisResult",
                "python": "result = client.analyze_repository(repo_id='repo-123', analysis_type='quality')",
                "typescript": "const result = client.analyzeRepository({ repoId: 'repo-123', analysisType: 'quality' })",
                "rest": "POST /api/v1/repositories/{repo_id}/analyze\nBody: { \"analysis_type\": \"quality\" }",
            },
            "list_agents": {
                "description": "List all available AI agents",
                "parameters": [{"name": "agent_type", "type": "string", "required": False, "description": "Filter by agent type"}],
                "returns": "list[Agent]",
                "python": "agents = client.list_agents(agent_type='code-reviewer')",
                "typescript": "const agents = client.listAgents({ agentType: 'code-reviewer' })",
                "rest": "GET /api/v1/agents?agent_type=code-reviewer",
            },
            "execute_agent": {
                "description": "Execute an agent task with the given prompt",
                "parameters": [{"name": "agent_id", "type": "string", "required": True, "description": "Agent ID"}, {"name": "prompt", "type": "string", "required": True, "description": "Task prompt"}, {"name": "context", "type": "dict", "required": False, "description": "Additional context"}],
                "returns": "AgentResult",
                "python": "result = client.execute_agent(agent_id='agent-123', prompt='Review this code')",
                "typescript": "const result = client.executeAgent({ agentId: 'agent-123', prompt: 'Review this code' })",
                "rest": "POST /api/v1/agents/{agent_id}/execute\nBody: { \"prompt\": \"Review this code\" }",
            },
            "search_memory": {
                "description": "Search the AI memory store for relevant context",
                "parameters": [{"name": "query", "type": "string", "required": True, "description": "Search query"}, {"name": "limit", "type": "integer", "required": False, "description": "Max results"}],
                "returns": "list[MemoryEntry]",
                "python": "results = client.search_memory(query='authentication patterns', limit=10)",
                "typescript": "const results = client.searchMemory({ query: 'authentication patterns', limit: 10 })",
                "rest": "GET /api/v1/memory/search?q=authentication+patterns&limit=10",
            },
            "create_workflow": {
                "description": "Create a new automation workflow",
                "parameters": [{"name": "name", "type": "string", "required": True, "description": "Workflow name"}, {"name": "steps", "type": "list", "required": True, "description": "Workflow steps"}, {"name": "trigger", "type": "dict", "required": False, "description": "Trigger configuration"}],
                "returns": "Workflow",
                "python": "wf = client.create_workflow(name='ci-pipeline', steps=[...])",
                "typescript": "const wf = client.createWorkflow({ name: 'ci-pipeline', steps: [...] })",
                "rest": "POST /api/v1/workflows\nBody: { \"name\": \"ci-pipeline\", \"steps\": [...] }",
            },
            "execute_workflow": {
                "description": "Execute a previously created workflow",
                "parameters": [{"name": "workflow_id", "type": "string", "required": True, "description": "Workflow ID"}, {"name": "params", "type": "dict", "required": False, "description": "Execution parameters"}],
                "returns": "WorkflowExecution",
                "python": "exec = client.execute_workflow(workflow_id='wf-123', params={})",
                "typescript": "const exec = client.executeWorkflow({ workflowId: 'wf-123', params: {} })",
                "rest": "POST /api/v1/workflows/{workflow_id}/execute\nBody: { \"params\": {} }",
            },
            "get_metrics": {
                "description": "Get monitoring metrics for agents, workflows, and system health",
                "parameters": [{"name": "metric_type", "type": "string", "required": False, "description": "Metric type (agents, workflows, system)"}, {"name": "time_range", "type": "string", "required": False, "description": "Time range (1h, 24h, 7d, 30d)"}],
                "returns": "Metrics",
                "python": "metrics = client.get_metrics(metric_type='agents', time_range='24h')",
                "typescript": "const metrics = client.getMetrics({ metricType: 'agents', timeRange: '24h' })",
                "rest": "GET /api/v1/metrics?type=agents&time_range=24h",
            },
        }
        for name, spec in defs.items():
            for lang in SDKLanguage:
                self._methods.setdefault(name, {})[lang] = SDKMethod(
                    name=name,
                    description=spec["description"],
                    parameters=spec["parameters"],
                    returns=spec["returns"],
                    example=spec[lang.value],
                )

    def _init_examples(self) -> None:
        self._examples = {
            "authentication": {
                SDKLanguage.PYTHON: [
                    "from forgeai import ForgeAIClient\n\nclient = ForgeAIClient(base_url='https://api.forgeai.dev')\ntoken = client.authenticate(api_key='your-api-key')\nprint(f'Authenticated: {token}')",
                ],
                SDKLanguage.TYPESCRIPT: [
                    "import { ForgeAIClient } from '@forgeai/sdk';\n\nconst client = new ForgeAIClient({ baseUrl: 'https://api.forgeai.dev' });\nconst token = await client.authenticate({ apiKey: 'your-api-key' });\nconsole.log(`Authenticated: ${token}`);",
                ],
                SDKLanguage.REST: [
                    "curl -X POST https://api.forgeai.dev/api/v1/auth/token \\\n  -H 'Content-Type: application/json' \\\n  -d '{\"api_key\": \"your-api-key\"}'",
                ],
            },
            "repository-analysis": {
                SDKLanguage.PYTHON: [
                    "client = ForgeAIClient(base_url='https://api.forgeai.dev', api_key='key')\nresult = client.analyze_repository(repo_id='repo-123', analysis_type='quality')\nprint(f'Score: {result.score}')\nfor issue in result.issues:\n    print(f'  - {issue.description}')",
                ],
                SDKLanguage.TYPESCRIPT: [
                    "const client = new ForgeAIClient({ baseUrl: 'https://api.forgeai.dev', apiKey: 'key' });\nconst result = await client.analyzeRepository({ repoId: 'repo-123', analysisType: 'quality' });\nconsole.log(`Score: ${result.score}`);\nresult.issues.forEach(issue => console.log(`  - ${issue.description}`));",
                ],
                SDKLanguage.REST: [
                    "curl -X POST https://api.forgeai.dev/api/v1/repositories/repo-123/analyze \\\n  -H 'Authorization: Bearer YOUR_TOKEN' \\\n  -H 'Content-Type: application/json' \\\n  -d '{\"analysis_type\": \"quality\"}'",
                ],
            },
            "agent-execution": {
                SDKLanguage.PYTHON: [
                    "result = client.execute_agent(\n    agent_id='code-reviewer-01',\n    prompt='Review the authentication module for security vulnerabilities',\n    context={'file_path': 'src/auth.py'}\n)\nprint(result.summary)\nfor finding in result.findings:\n    print(f'[{finding.severity}] {finding.message}')",
                ],
                SDKLanguage.TYPESCRIPT: [
                    "const result = await client.executeAgent({\n  agentId: 'code-reviewer-01',\n  prompt: 'Review the authentication module for security vulnerabilities',\n  context: { filePath: 'src/auth.py' }\n});\nconsole.log(result.summary);\nresult.findings.forEach(f => console.log(`[${f.severity}] ${f.message}`));",
                ],
                SDKLanguage.REST: [
                    "curl -X POST https://api.forgeai.dev/api/v1/agents/code-reviewer-01/execute \\\n  -H 'Authorization: Bearer YOUR_TOKEN' \\\n  -H 'Content-Type: application/json' \\\n  -d '{\"prompt\": \"Review the authentication module\", \"context\": {\"file_path\": \"src/auth.py\"}}'",
                ],
            },
        }

    def get_python_sdk(self) -> dict:
        return {
            "language": "python",
            "package": "forgeai",
            "install": "pip install forgeai",
            "version": "1.0.0",
            "base_class": "ForgeAIClient",
            "methods": [m[SDKLanguage.PYTHON] for m in self._methods.values()],
        }

    def get_typescript_sdk(self) -> dict:
        return {
            "language": "typescript",
            "package": "@forgeai/sdk",
            "install": "npm install @forgeai/sdk",
            "version": "1.0.0",
            "base_class": "ForgeAIClient",
            "methods": [m[SDKLanguage.TYPESCRIPT] for m in self._methods.values()],
        }

    def get_rest_api(self) -> dict:
        return {
            "language": "rest",
            "base_url": "https://api.forgeai.dev/api/v1",
            "auth": "Bearer token in Authorization header",
            "version": "1.0.0",
            "methods": [m[SDKLanguage.REST] for m in self._methods.values()],
        }

    def get_method_docs(self, language: SDKLanguage, method: str) -> SDKMethod:
        if method not in self._methods:
            raise KeyError(f"Method '{method}' not found")
        if language not in self._methods[method]:
            raise KeyError(f"Method '{method}' not available for {language.value}")
        return self._methods[method][language]

    def get_examples(self, language: SDKLanguage, feature: str) -> list[str]:
        if feature not in self._examples:
            raise KeyError(f"Feature '{feature}' not found")
        return self._examples[feature].get(language, [])

    def get_quickstart(self, language: SDKLanguage) -> str:
        quickstarts = {
            SDKLanguage.PYTHON: (
                "# ForgeAI Python SDK Quickstart\n\n"
                "## Installation\n"
                "```bash\npip install forgeai\n```\n\n"
                "## Basic Usage\n"
                "```python\nfrom forgeai import ForgeAIClient\n\n"
                "# Initialize client\nclient = ForgeAIClient(\n"
                "    base_url='https://api.forgeai.dev',\n"
                "    api_key='your-api-key'\n)\n\n"
                "# Authenticate\ntoken = client.authenticate(api_key='your-api-key')\n\n"
                "# List repositories\nrepos = client.list_repositories()\nfor repo in repos:\n"
                "    print(repo.name)\n\n"
                "# Analyze a repository\nresult = client.analyze_repository(repo_id='repo-123')\n"
                "print(f'Quality Score: {result.score}')\n\n"
                "# Execute an agent\nreview = client.execute_agent(\n"
                "    agent_id='code-reviewer-01',\n"
                "    prompt='Review this code for issues'\n)\n"
                "print(review.summary)\n```"
            ),
            SDKLanguage.TYPESCRIPT: (
                "# ForgeAI TypeScript SDK Quickstart\n\n"
                "## Installation\n"
                "```bash\nnpm install @forgeai/sdk\n```\n\n"
                "## Basic Usage\n"
                "```typescript\nimport { ForgeAIClient } from '@forgeai/sdk';\n\n"
                "// Initialize client\nconst client = new ForgeAIClient({\n"
                "    baseUrl: 'https://api.forgeai.dev',\n"
                "    apiKey: 'your-api-key'\n});\n\n"
                "// Authenticate\nconst token = await client.authenticate({ apiKey: 'your-api-key' });\n\n"
                "// List repositories\nconst repos = await client.listRepositories();\n"
                "repos.forEach(repo => console.log(repo.name));\n\n"
                "// Analyze a repository\nconst result = await client.analyzeRepository({ repoId: 'repo-123' });\n"
                "console.log(`Quality Score: ${result.score}`);\n\n"
                "// Execute an agent\nconst review = await client.executeAgent({\n"
                "    agentId: 'code-reviewer-01',\n"
                "    prompt: 'Review this code for issues'\n});\n"
                "console.log(review.summary);\n```"
            ),
            SDKLanguage.REST: (
                "# ForgeAI REST API Quickstart\n\n"
                "## Base URL\n"
                "```\nhttps://api.forgeai.dev/api/v1\n```\n\n"
                "## Authentication\n"
                "```bash\n# Get access token\ncurl -X POST https://api.forgeai.dev/api/v1/auth/token \\\n"
                "  -H 'Content-Type: application/json' \\\n"
                "  -d '{\"api_key\": \"your-api-key\"}'\n```\n\n"
                "## List Repositories\n"
                "```bash\ncurl -X GET https://api.forgeai.dev/api/v1/repositories \\\n"
                "  -H 'Authorization: Bearer YOUR_TOKEN'\n```\n\n"
                "## Analyze Repository\n"
                "```bash\ncurl -X POST https://api.forgeai.dev/api/v1/repositories/repo-123/analyze \\\n"
                "  -H 'Authorization: Bearer YOUR_TOKEN' \\\n"
                "  -H 'Content-Type: application/json' \\\n"
                "  -d '{\"analysis_type\": \"quality\"}'\n```\n\n"
                "## Execute Agent\n"
                "```bash\ncurl -X POST https://api.forgeai.dev/api/v1/agents/code-reviewer-01/execute \\\n"
                "  -H 'Authorization: Bearer YOUR_TOKEN' \\\n"
                "  -H 'Content-Type: application/json' \\\n"
                "  -d '{\"prompt\": \"Review this code for issues\"}'\n```"
            ),
        }
        return quickstarts[language]


sdk_docs = SDKDocumentation()
