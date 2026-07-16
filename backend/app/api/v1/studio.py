"""Studio API endpoints for the visual AI Engineering Platform.

Provides endpoints for workflow building, prompt management,
execution replay, agent management, and workspace operations.
"""

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.studio.workflow_builder import WorkflowBuilderService, NodeType, WorkflowNode, WorkflowEdge
from app.studio.prompt_manager import PromptManagerService
from app.studio.replay_service import ReplayService
from app.studio.agent_manager import AgentManagerService
from app.studio.workspace_manager import WorkspaceManagerService
from app.schemas.common import BaseResponse, ResponseStatus

router = APIRouter(prefix="/studio", tags=["Studio"])

# Singleton services
_workflow_builder: WorkflowBuilderService | None = None
_prompt_manager: PromptManagerService | None = None
_replay_service: ReplayService | None = None
_agent_manager: AgentManagerService | None = None
_workspace_manager: WorkspaceManagerService | None = None


def _get_services() -> dict[str, Any]:
    global _workflow_builder, _prompt_manager, _replay_service
    global _agent_manager, _workspace_manager

    if _workflow_builder is None:
        _workflow_builder = WorkflowBuilderService()
    if _prompt_manager is None:
        _prompt_manager = PromptManagerService()
    if _replay_service is None:
        _replay_service = ReplayService()
    if _agent_manager is None:
        _agent_manager = AgentManagerService()
    if _workspace_manager is None:
        _workspace_manager = WorkspaceManagerService()

    return {
        "workflow_builder": _workflow_builder,
        "prompt_manager": _prompt_manager,
        "replay_service": _replay_service,
        "agent_manager": _agent_manager,
        "workspace_manager": _workspace_manager,
    }


# ── Request Models ─────────────────────────────────────────────────────


class CreatePromptRequest(BaseModel):
    name: str = Field(..., description="Prompt name")
    description: str = Field(default="", description="Prompt description")
    content: str = Field(..., description="Prompt content")
    variables: list[str] = Field(default_factory=list, description="Template variables")
    tags: list[str] = Field(default_factory=list, description="Tags")


class UpdatePromptRequest(BaseModel):
    content: str = Field(..., description="Updated prompt content")
    comment: str = Field(default="", description="Version comment")


class TestPromptRequest(BaseModel):
    model: str = Field(default="qwen2.5", description="Model to test with")
    input_vars: dict[str, str] = Field(default_factory=dict, description="Input variables")


class AgentConfigRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    prompt_template: str | None = None
    capabilities: list[str] | None = None
    tools: list[str] | None = None


class WorkflowNodeRequest(BaseModel):
    type: str = Field(..., description="Node type")
    label: str = Field(..., description="Node label")
    position_x: float = Field(default=0, description="X position")
    position_y: float = Field(default=0, description="Y position")
    data: dict[str, Any] = Field(default_factory=dict, description="Node data")


class WorkflowEdgeRequest(BaseModel):
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    label: str = Field(default="", description="Edge label")


class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    types: list[str] = Field(default_factory=list, description="Filter by types")


# ── Workflow Builder Endpoints ─────────────────────────────────────────


@router.get("/workflows", response_model=BaseResponse[list[dict[str, Any]]])
async def list_workflows():
    """List available workflows for the builder."""
    services = _get_services()
    try:
        # Get workflow graphs from the builder service
        # For now, return empty list as we need workflow data
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message="Workflows retrieved",
            data=[],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workflows/{workflow_id}/graph", response_model=BaseResponse[dict[str, Any]])
async def get_workflow_graph(workflow_id: str):
    """Get visual graph representation of a workflow."""
    services = _get_services()
    try:
        graph = await services["workflow_builder"].get_workflow_graph(workflow_id)
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message="Workflow graph retrieved",
            data={
                "nodes": [
                    {
                        "id": n.id,
                        "type": n.type.value if hasattr(n.type, "value") else n.type,
                        "label": n.label,
                        "position": {"x": n.position.x, "y": n.position.y},
                        "data": n.data,
                        "status": n.status,
                    }
                    for n in graph.nodes
                ],
                "edges": [
                    {
                        "id": e.id,
                        "source": e.source,
                        "target": e.target,
                        "label": e.label,
                    }
                    for e in graph.edges
                ],
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class ExecuteWorkflowRequest(BaseModel):
    nodes: list[dict[str, Any]] = Field(..., description="Workflow nodes")
    edges: list[dict[str, Any]] = Field(..., description="Workflow edges")
    inputs: dict[str, Any] = Field(default_factory=dict, description="Initial workflow inputs")


class NodeExecutionResult(BaseModel):
    node_id: str
    node_type: str = ""
    label: str = ""
    status: str
    output: dict[str, Any] = Field(default_factory=dict)
    duration_ms: int = 0
    error: str | None = None
    llm_model: str | None = None
    tokens_used: int = 0


class WorkflowExecutionResult(BaseModel):
    execution_id: str
    status: str
    node_results: list[NodeExecutionResult]
    final_output: dict[str, Any] = Field(default_factory=dict)
    total_duration_ms: int = 0


@router.post("/workflows/execute")
async def execute_workflow(request: ExecuteWorkflowRequest):
    """Execute a workflow graph with real LLM calls, streaming results as SSE.

    Each SSE event is a JSON line with a ``type`` field:
      - ``node_start``: a node is beginning execution
      - ``node_complete``: a node finished successfully
      - ``node_error``: a node failed
      - ``workflow_complete``: entire workflow finished
    """
    from fastapi.responses import StreamingResponse
    from app.studio.workflow_engine import WorkflowExecutionEngine

    engine = WorkflowExecutionEngine()

    async def event_stream():
        async for event in engine.execute_workflow(
            nodes=request.nodes,
            edges=request.edges,
            inputs=request.inputs,
        ):
            yield f"data: {__import__('json').dumps(event, default=str)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/workflows/node-templates", response_model=BaseResponse[list[dict[str, Any]]])
async def get_node_templates():
    """Get available node types for the workflow builder."""
    services = _get_services()
    try:
        templates = await services["workflow_builder"].get_node_templates()
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message="Node templates retrieved",
            data=templates,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/workflows/validate", response_model=BaseResponse[dict[str, Any]])
async def validate_workflow(nodes: list[dict], edges: list[dict]):
    """Validate a workflow graph."""
    services = _get_services()
    try:
        from app.studio.workflow_builder import WorkflowGraph, WorkflowNode, WorkflowEdge, NodeType
        from app.studio.workflow_builder import NodePosition

        node_objects = []
        for n in nodes:
            node_objects.append(WorkflowNode(
                id=n["id"],
                type=NodeType(n["type"]),
                label=n["label"],
                position=NodePosition(x=n.get("position", {}).get("x", 0), y=n.get("position", {}).get("y", 0)),
                data=n.get("data", {}),
                status=n.get("status", "idle"),
            ))

        edge_objects = []
        for e in edges:
            edge_objects.append(WorkflowEdge(
                id=e.get("id", str(uuid.uuid4())),
                source=e["source"],
                target=e["target"],
                label=e.get("label", ""),
            ))

        graph = WorkflowGraph(nodes=node_objects, edges=edge_objects)
        result = await services["workflow_builder"].validate_graph(graph)
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message="Validation complete",
            data=result,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Studio Workflow Persistence ────────────────────────────────────────

_STUDIO_WORKFLOWS: list[dict[str, Any]] = []


def _load_studio_workflows():
    """Load studio workflows from disk on startup."""
    try:
        from app.persistence import load_studio_workflows
        saved = load_studio_workflows()
        _STUDIO_WORKFLOWS.extend(saved)
    except Exception:
        pass


def _persist_studio_workflows():
    """Save studio workflows to disk."""
    try:
        from app.persistence import save_studio_workflows
        save_studio_workflows(_STUDIO_WORKFLOWS)
    except Exception:
        pass


class SaveStudioWorkflowRequest(BaseModel):
    name: str = Field(..., description="Workflow name")
    description: str = Field(default="", description="Workflow description")
    project_id: str | None = Field(default=None, description="Associated project ID")
    nodes: list[dict[str, Any]] = Field(default_factory=list, description="Workflow nodes")
    edges: list[dict[str, Any]] = Field(default_factory=list, description="Workflow edges")


@router.get("/workflows/list", response_model=BaseResponse[list[dict[str, Any]]])
async def list_studio_workflows(project_id: str | None = None):
    """List saved studio workflows, optionally filtered by project_id."""
    workflows = _STUDIO_WORKFLOWS
    if project_id:
        workflows = [w for w in workflows if w.get("project_id") == project_id]
    return BaseResponse(
        status=ResponseStatus.SUCCESS,
        message=f"Found {len(workflows)} workflows",
        data=workflows,
    )


@router.post("/workflows/save", response_model=BaseResponse[dict[str, Any]])
async def save_studio_workflow(request: SaveStudioWorkflowRequest):
    """Save a studio workflow graph to disk."""
    workflow_id = str(uuid.uuid4())
    workflow = {
        "id": workflow_id,
        "name": request.name,
        "description": request.description,
        "project_id": request.project_id,
        "nodes": request.nodes,
        "edges": request.edges,
        "created_at": __import__("datetime").datetime.now(__import__("datetime").UTC).isoformat(),
        "updated_at": __import__("datetime").datetime.now(__import__("datetime").UTC).isoformat(),
    }
    _STUDIO_WORKFLOWS.insert(0, workflow)
    _persist_studio_workflows()
    return BaseResponse(
        status=ResponseStatus.SUCCESS,
        message="Workflow saved",
        data=workflow,
    )


@router.put("/workflows/{workflow_id}", response_model=BaseResponse[dict[str, Any]])
async def update_studio_workflow(workflow_id: str, request: SaveStudioWorkflowRequest):
    """Update an existing studio workflow."""
    workflow = next((w for w in _STUDIO_WORKFLOWS if w["id"] == workflow_id), None)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    workflow["name"] = request.name
    workflow["description"] = request.description
    workflow["project_id"] = request.project_id
    workflow["nodes"] = request.nodes
    workflow["edges"] = request.edges
    workflow["updated_at"] = __import__("datetime").datetime.now(__import__("datetime").UTC).isoformat()
    _persist_studio_workflows()
    return BaseResponse(
        status=ResponseStatus.SUCCESS,
        message="Workflow updated",
        data=workflow,
    )


@router.delete("/workflows/{workflow_id}")
async def delete_studio_workflow(workflow_id: str):
    """Delete a studio workflow."""
    global _STUDIO_WORKFLOWS
    before = len(_STUDIO_WORKFLOWS)
    _STUDIO_WORKFLOWS = [w for w in _STUDIO_WORKFLOWS if w["id"] != workflow_id]
    if len(_STUDIO_WORKFLOWS) == before:
        raise HTTPException(status_code=404, detail="Workflow not found")
    _persist_studio_workflows()
    return BaseResponse(
        status=ResponseStatus.SUCCESS,
        message="Workflow deleted",
    )


# Load on module import
_load_studio_workflows()


# ── Prompt Studio Endpoints ────────────────────────────────────────────


@router.get("/prompts", response_model=BaseResponse[list[dict[str, Any]]])
async def list_prompts():
    """List all prompts."""
    services = _get_services()
    try:
        prompts = await services["prompt_manager"].list_prompts()
        data = [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "content": p.content,
                "variables": p.variables,
                "current_version": p.current_version,
                "tags": p.tags,
                "versions_count": len(p.versions),
            }
            for p in prompts
        ]
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message=f"Found {len(data)} prompts",
            data=data,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/prompts/{prompt_id}", response_model=BaseResponse[dict[str, Any]])
async def get_prompt(prompt_id: str):
    """Get prompt details with version history."""
    services = _get_services()
    try:
        prompt = await services["prompt_manager"].get_prompt(prompt_id)
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message="Prompt retrieved",
            data={
                "id": prompt.id,
                "name": prompt.name,
                "description": prompt.description,
                "content": prompt.content,
                "variables": prompt.variables,
                "current_version": prompt.current_version,
                "tags": prompt.tags,
                "versions": [
                    {"version": v.version, "created_by": v.created_by, "created_at": v.created_at.isoformat(), "comment": v.comment}
                    for v in prompt.versions
                ],
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/prompts", response_model=BaseResponse[dict[str, str]])
async def create_prompt(request: CreatePromptRequest):
    """Create a new prompt."""
    services = _get_services()
    try:
        prompt_id = await services["prompt_manager"].create_prompt(
            name=request.name,
            description=request.description,
            content=request.content,
            variables=request.variables,
            tags=request.tags,
        )
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message="Prompt created",
            data={"prompt_id": prompt_id},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/prompts/{prompt_id}", response_model=BaseResponse[dict[str, str]])
async def update_prompt(prompt_id: str, request: UpdatePromptRequest):
    """Update prompt content (creates new version)."""
    services = _get_services()
    try:
        version = await services["prompt_manager"].update_prompt(
            prompt_id=prompt_id,
            content=request.content,
            comment=request.comment,
        )
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message=f"Updated to version {version}",
            data={"version": str(version)},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/prompts/{prompt_id}/test", response_model=BaseResponse[dict[str, Any]])
async def test_prompt(prompt_id: str, request: TestPromptRequest):
    """Test a prompt with a model."""
    services = _get_services()
    try:
        result = await services["prompt_manager"].test_prompt(
            prompt_id=prompt_id,
            model=request.model,
            input_vars=request.input_vars,
        )
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message="Prompt tested",
            data={
                "output": result.output,
                "tokens_used": result.tokens_used,
                "latency_ms": result.latency_ms,
                "confidence": result.confidence,
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/prompts/{prompt_id}/history", response_model=BaseResponse[list[dict[str, Any]]])
async def get_prompt_history(prompt_id: str):
    """Get prompt version history."""
    services = _get_services()
    try:
        history = await services["prompt_manager"].get_prompt_history(prompt_id)
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message="Prompt history retrieved",
            data=[
                {"version": v.version, "created_by": v.created_by, "created_at": v.created_at.isoformat(), "comment": v.comment}
                for v in history
            ],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/prompts/{prompt_id}/rollback", response_model=BaseResponse[dict[str, str]])
async def rollback_prompt(prompt_id: str, version: int):
    """Rollback prompt to a specific version."""
    services = _get_services()
    try:
        await services["prompt_manager"].rollback_prompt(prompt_id, version)
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message=f"Rolled back to version {version}",
            data={"version": str(version)},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Replay Endpoints ───────────────────────────────────────────────────


@router.get("/replay/{execution_id}", response_model=BaseResponse[dict[str, Any]])
async def get_replay(execution_id: str):
    """Get replay state for an execution."""
    services = _get_services()
    try:
        state = await services["replay_service"].get_replay(execution_id)
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message="Replay state retrieved",
            data={
                "execution_id": state.execution_id,
                "workflow_id": state.workflow_id,
                "current_index": state.current_index,
                "status": state.status.value if hasattr(state.status, "value") else state.status,
                "total_events": len(state.events),
                "speed": state.speed,
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/replay/{execution_id}/events", response_model=BaseResponse[list[dict[str, Any]]])
async def get_replay_events(execution_id: str):
    """Get all replay events."""
    services = _get_services()
    try:
        events = await services["replay_service"].get_events(execution_id)
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message="Replay events retrieved",
            data=[
                {
                    "timestamp": e.timestamp.isoformat(),
                    "event_type": e.event_type,
                    "node_id": e.node_id,
                    "agent_id": e.agent_id,
                    "tool_id": e.tool_id,
                    "data": e.data,
                    "duration_ms": e.duration_ms,
                }
                for e in events
            ],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/replay/{execution_id}/step-forward", response_model=BaseResponse[dict[str, Any] | None])
async def step_forward(execution_id: str):
    """Step forward in replay."""
    services = _get_services()
    try:
        event = await services["replay_service"].step_forward(execution_id)
        if event:
            return BaseResponse(
                status=ResponseStatus.SUCCESS,
                message="Stepped forward",
                data={
                    "timestamp": event.timestamp.isoformat(),
                    "event_type": event.event_type,
                    "node_id": event.node_id,
                    "data": event.data,
                },
            )
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message="No more events",
            data=None,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Agent Playground Endpoints ─────────────────────────────────────────


@router.get("/agents", response_model=BaseResponse[list[dict[str, Any]]])
async def list_agents():
    """List all agents for the playground."""
    services = _get_services()
    try:
        agents = await services["agent_manager"].list_agents()
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message=f"Found {len(agents)} agents",
            data=agents,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/{agent_id}", response_model=BaseResponse[dict[str, Any]])
async def get_agent(agent_id: str):
    """Get agent details."""
    services = _get_services()
    try:
        agent = await services["agent_manager"].get_agent(agent_id)
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message="Agent retrieved",
            data=agent,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/agents/{agent_id}/config", response_model=BaseResponse[dict[str, str]])
async def update_agent_config(agent_id: str, request: AgentConfigRequest):
    """Update agent configuration."""
    services = _get_services()
    try:
        from app.studio.agent_manager import AgentConfig
        config = AgentConfig(
            name=request.name or "",
            description=request.description or "",
            prompt_template=request.prompt_template or "",
            capabilities=request.capabilities or [],
            tools=request.tools or [],
        )
        await services["agent_manager"].update_agent_config(agent_id, config)
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message="Agent config updated",
            data={"agent_id": agent_id},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/{agent_id}/performance", response_model=BaseResponse[dict[str, Any]])
async def get_agent_performance(agent_id: str):
    """Get agent performance metrics."""
    services = _get_services()
    try:
        perf = await services["agent_manager"].get_agent_performance(agent_id)
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message="Agent performance retrieved",
            data={
                "tasks_completed": perf.tasks_completed,
                "tasks_failed": perf.tasks_failed,
                "avg_duration": perf.avg_duration,
                "success_rate": perf.success_rate,
                "last_active": perf.last_active.isoformat() if perf.last_active else None,
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agents/{agent_id}/test", response_model=BaseResponse[dict[str, Any]])
async def test_agent(agent_id: str, prompt: str, repository_id: str = ""):
    """Test an agent with a prompt."""
    services = _get_services()
    try:
        result = await services["agent_manager"].test_agent(agent_id, prompt, repository_id)
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message="Agent tested",
            data=result,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Workspace Endpoints ────────────────────────────────────────────────


@router.get("/workspace", response_model=BaseResponse[dict[str, Any]])
async def get_workspace():
    """Get workspace overview."""
    services = _get_services()
    try:
        overview = await services["workspace_manager"].get_workspace_overview()
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message="Workspace retrieved",
            data=overview,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workspace/search", response_model=BaseResponse[list[dict[str, Any]]])
async def search_workspace(query: str, types: str = ""):
    """Search across all workspace items."""
    services = _get_services()
    try:
        type_list = [t.strip() for t in types.split(",") if t.strip()] if types else []
        items = await services["workspace_manager"].search(query, type_list)
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message=f"Found {len(items)} items",
            data=[
                {
                    "id": i.id,
                    "type": i.type,
                    "name": i.name,
                    "description": i.description,
                    "updated_at": i.updated_at.isoformat(),
                }
                for i in items
            ],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workspace/recent", response_model=BaseResponse[list[dict[str, Any]]])
async def get_recent_items(limit: int = 20):
    """Get recently accessed items."""
    services = _get_services()
    try:
        items = await services["workspace_manager"].get_recent_items(limit)
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message="Recent items retrieved",
            data=[
                {
                    "id": i.id,
                    "type": i.type,
                    "name": i.name,
                    "description": i.description,
                    "updated_at": i.updated_at.isoformat(),
                }
                for i in items
            ],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workspace/bookmarks", response_model=BaseResponse[list[dict[str, Any]]])
async def get_bookmarks():
    """Get bookmarked items."""
    services = _get_services()
    try:
        items = await services["workspace_manager"].get_bookmarks()
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message="Bookmarks retrieved",
            data=[
                {
                    "id": i.id,
                    "type": i.type,
                    "name": i.name,
                    "description": i.description,
                }
                for i in items
            ],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
