"""FastAPI application factory for the ForgeAI backend."""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI

from app.ai.clients.ollama import OllamaClient
from app.ai.config import get_ai_settings
from app.ai.controllers.chat_controller import ChatController
from app.ai.memory.conversation import ConversationManager
from app.ai.models.model_manager import ModelManager
from app.ai.prompts.registry import PromptRegistry
from app.ai.streaming.handler import StreamingHandler
from app.core.config import get_settings
from app.core.logging import get_logger, setup_logging
from app.database.session import close_db, init_db
from app.exceptions.handlers import register_exception_handlers
from app.memory.config import get_memory_settings
from app.memory.memory_service import MemoryService
from app.planner.config import get_planner_settings
from app.planner.planner_service import PlannerService
from app.repo_intelligence.config import get_repo_settings
from app.repo_intelligence.services.analysis_service import AnalysisService
from app.repo_intelligence.services.repository_service import RepositoryService
from app.agents.config import get_agent_settings
from app.agents.tools.factory import create_tool_registry
from app.agents.orchestrator import AgentOrchestrator
from app.agents.registry import AgentRegistry
from app.agents.implementations import (
    PlannerAgent,
    ExecutorAgent,
    ReviewerAgent,
    ResearcherAgent,
)
from app.agents.schemas import AgentType
from app.workflows.config import get_workflow_settings
from app.workflows.workflow_service import WorkflowService
from app.workflows.repository import WorkflowRepository
from app.agents.enterprise.runtime import AgentRuntime
from app.tools import (
    ToolRegistry,
    PermissionEngine,
    ToolEventEmitter,
    FilesystemTool,
    GitTool,
    TerminalTool,
    DockerTool,
    DatabaseTool,
    BrowserTool,
)
from app.tools.runtime import ToolRuntime
from app.agents.software_engineer.software_engineer import SoftwareEngineerAgent
from app.agents.qa.qa_agent import QAAgent
from app.agents.documentation.documentation_agent import DocumentationAgent
from app.execution.execution_runtime import ExecutionRuntime
from app.approval.approval_engine import ApprovalEngine
from app.approval.timeout_manager import TimeoutManager
from fastapi.middleware.cors import CORSMiddleware

from app.middleware import RequestIdMiddleware
from app.schemas.common import HealthResponse
from app.api.v1.router import router as v1_router

settings = get_settings()
ai_settings = get_ai_settings()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application startup and shutdown lifecycle.

    On startup:
        - Initialize structured logging.
        - Create database tables.
        - Initialize AI components (Ollama client, model manager, etc.).

    On shutdown:
        - Close Ollama client connections.
        - Dispose the database connection pool.
    """
    setup_logging(log_level=settings.LOG_LEVEL, log_format=settings.LOG_FORMAT)
    await init_db()

    ollama_client = OllamaClient(
        base_url=ai_settings.OLLAMA_BASE_URL,
        timeout=ai_settings.OLLAMA_TIMEOUT,
        connect_timeout=ai_settings.OLLAMA_CONNECT_TIMEOUT,
    )
    model_manager = ModelManager(ollama_client=ollama_client, settings=ai_settings)
    prompt_registry = PromptRegistry()
    conversation_manager = ConversationManager(settings=ai_settings)
    streaming_handler = StreamingHandler()
    chat_controller = ChatController(
        ollama_client=ollama_client,
        model_manager=model_manager,
        prompt_registry=prompt_registry,
        conversation_manager=conversation_manager,
        streaming_handler=streaming_handler,
        settings=ai_settings,
    )

    app.state.ollama_client = ollama_client
    app.state.model_manager = model_manager
    app.state.prompt_registry = prompt_registry
    app.state.conversation_manager = conversation_manager
    app.state.streaming_handler = streaming_handler
    app.state.chat_controller = chat_controller
    app.state.settings = ai_settings

    logger.info(
        "AI components initialized: ollama_url=%s default_model=%s",
        ai_settings.OLLAMA_BASE_URL,
        ai_settings.DEFAULT_MODEL,
    )

    repo_settings = get_repo_settings()
    analysis_service = AnalysisService(settings=repo_settings)
    repo_service = RepositoryService(settings=repo_settings, analysis_service=analysis_service)

    app.state.repo_settings = repo_settings
    app.state.analysis_service = analysis_service
    app.state.repo_service = repo_service

    logger.info("Repository intelligence components initialized")

    memory_settings = get_memory_settings()
    memory_service = MemoryService(settings=memory_settings)

    app.state.memory_settings = memory_settings
    app.state.memory_service = memory_service

    logger.info("Memory components initialized")

    planner_settings = get_planner_settings()
    planner_service = PlannerService()

    app.state.planner_settings = planner_settings
    app.state.planner_service = planner_service

    logger.info("Planner components initialized")

    agent_settings = get_agent_settings()
    tool_registry = create_tool_registry()
    agent_registry = AgentRegistry(tool_registry=tool_registry)
    agent_orchestrator = AgentOrchestrator(tool_registry=tool_registry)

    agent_registry.register_agent_type(AgentType.PLANNER, PlannerAgent)
    agent_registry.register_agent_type(AgentType.EXECUTOR, ExecutorAgent)
    agent_registry.register_agent_type(AgentType.REVIEWER, ReviewerAgent)
    agent_registry.register_agent_type(AgentType.RESEARCHER, ResearcherAgent)

    for agent_type in agent_registry.get_available_types():
        agent_registry.create_agent(agent_type)

    app.state.agent_settings = agent_settings
    app.state.tool_registry = tool_registry
    app.state.agent_registry = agent_registry
    app.state.agent_orchestrator = agent_orchestrator

    logger.info("Agents components initialized")

    workflow_settings = get_workflow_settings()
    workflow_repository = None
    workflow_service = None

    app.state.workflow_settings = workflow_settings
    app.state.workflow_repository = workflow_repository
    app.state.workflow_service = workflow_service

    logger.info("Workflows components initialized")

    agent_runtime = AgentRuntime()

    app.state.agent_runtime = agent_runtime

    logger.info("Agent Runtime initialized with %d agents", len(agent_runtime.list_agents()))

    # Initialize Tool Virtualization Layer
    tool_registry = ToolRegistry()
    permission_engine = PermissionEngine()
    tool_event_emitter = ToolEventEmitter()
    tool_runtime = ToolRuntime(
        registry=tool_registry,
        permission_engine=permission_engine,
        event_emitter=tool_event_emitter,
    )

    # Register MCP tools
    await tool_registry.register(FilesystemTool())
    await tool_registry.register(GitTool())
    await tool_registry.register(TerminalTool())
    await tool_registry.register(DockerTool())
    await tool_registry.register(DatabaseTool())
    await tool_registry.register(BrowserTool())

    app.state.tool_registry = tool_registry
    app.state.permission_engine = permission_engine
    app.state.tool_event_emitter = tool_event_emitter
    app.state.tool_runtime = tool_runtime

    logger.info("Tool Virtualization Layer initialized with %d tools", len(tool_registry.list_tools()))

    # Initialize Software Engineer Agent
    software_engineer = SoftwareEngineerAgent()
    app.state.software_engineer = software_engineer
    logger.info("Software Engineer Agent initialized")

    # Initialize Review Pipeline Agents
    qa_agent = QAAgent()
    documentation_agent = DocumentationAgent()

    app.state.qa_agent = qa_agent
    app.state.documentation_agent = documentation_agent

    logger.info("Review Pipeline Agents initialized")

    # Initialize Approval Engine
    approval_engine = ApprovalEngine()
    timeout_manager = TimeoutManager(approval_engine)
    await timeout_manager.start()

    app.state.approval_engine = approval_engine
    app.state.timeout_manager = timeout_manager
    logger.info("Approval Engine initialized")

    # Initialize Execution Runtime
    execution_runtime = ExecutionRuntime(approval_engine=approval_engine)
    app.state.execution_runtime = execution_runtime
    logger.info("Execution Runtime initialized")

    yield

    await streaming_handler.stop_all()
    await ollama_client.close()
    await tool_runtime.cleanup()
    await timeout_manager.stop()
    await close_db()


def create_application() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        A fully configured ``FastAPI`` instance with middleware,
        exception handlers, and routers attached.
    """
    application = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Total-Count", "X-Total-Pages"],
    )
    application.add_middleware(RequestIdMiddleware)

    register_exception_handlers(application)

    application.include_router(v1_router, prefix=settings.API_V1_PREFIX)

    @application.get("/health", response_model=HealthResponse, tags=["Health"])
    async def health_check() -> HealthResponse:
        """Return application health status including version and environment."""
        return HealthResponse(
            status="healthy",
            version=settings.APP_VERSION,
            environment=settings.APP_ENV,
        )

    return application


app = create_application()
