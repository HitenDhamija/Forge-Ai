"""Real workflow execution engine that chains nodes with LLM calls and data flow."""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from typing import Any

from app.ai.clients.ollama import OllamaClient
from app.ai.config import AISettings, get_ai_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class NodeResult:
    """Result of executing a single workflow node."""

    node_id: str
    node_type: str
    label: str
    status: str  # "completed" | "failed"
    output: dict[str, Any] = field(default_factory=dict)
    duration_ms: int = 0
    error: str | None = None
    llm_model: str | None = None
    tokens_used: int = 0


@dataclass
class WorkflowExecutionResult:
    """Full result of executing a workflow."""

    execution_id: str
    status: str  # "completed" | "failed"
    node_results: list[NodeResult]
    final_output: dict[str, Any] = field(default_factory=dict)
    total_duration_ms: int = 0


# ── Prompt builders per node type ──────────────────────────────────────


def _build_planner_prompt(
    label: str, data: dict[str, Any], parent_outputs: dict[str, Any]
) -> list[dict[str, str]]:
    context = _format_parent_outputs(parent_outputs)
    return [
        {
            "role": "system",
            "content": (
                "You are a task planning agent. Given a goal, produce a concise plan "
                "as a JSON object with keys: goal (string), steps (list of objects with "
                "title and description), risks (list of strings), estimated_complexity "
                "(low|medium|high). Return ONLY valid JSON, no markdown."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Goal: {label}\n"
                f"Configuration: {json.dumps(data, default=str)}\n"
                f"Context from previous steps:\n{context}"
            ),
        },
    ]


def _build_supervisor_prompt(
    label: str, data: dict[str, Any], parent_outputs: dict[str, Any]
) -> list[dict[str, str]]:
    context = _format_parent_outputs(parent_outputs)
    return [
        {
            "role": "system",
            "content": (
                "You are a supervisor agent monitoring workflow execution. Analyze the "
                "work done so far and provide a quality assessment. Return ONLY valid JSON "
                "with keys: status (approved|needs_revision|rejected), feedback (string), "
                "quality_score (0.0-1.0), recommendations (list of strings). No markdown."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Supervision task: {label}\n"
                f"Configuration: {json.dumps(data, default=str)}\n"
                f"Work completed so far:\n{context}"
            ),
        },
    ]


def _build_agent_prompt(
    label: str, data: dict[str, Any], parent_outputs: dict[str, Any]
) -> list[dict[str, str]]:
    role = data.get("role", "general assistant")
    context = _format_parent_outputs(parent_outputs)
    return [
        {
            "role": "system",
            "content": (
                f"You are an AI agent with the role: {role}. "
                "Execute the given task using the provided context. Be concise and actionable. "
                "Return your response as valid JSON with keys: result (string), "
                "confidence (0.0-1.0), actions_taken (list of strings). No markdown."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Task: {label}\n"
                f"Context from previous steps:\n{context}"
            ),
        },
    ]


def _build_decision_prompt(
    label: str, data: dict[str, Any], parent_outputs: dict[str, Any]
) -> list[dict[str, str]]:
    condition = data.get("condition", "evaluate the input")
    context = _format_parent_outputs(parent_outputs)
    return [
        {
            "role": "system",
            "content": (
                "You are a decision node in a workflow. Evaluate the given condition "
                "against the context and decide which branch to take. Return ONLY valid JSON "
                "with keys: decision (string - the chosen branch), reasoning (string), "
                "confidence (0.0-1.0). No markdown."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Decision: {label}\n"
                f"Condition to evaluate: {condition}\n"
                f"Context:\n{context}"
            ),
        },
    ]


def _build_reflection_prompt(
    label: str, data: dict[str, Any], parent_outputs: dict[str, Any]
) -> list[dict[str, str]]:
    context = _format_parent_outputs(parent_outputs)
    return [
        {
            "role": "system",
            "content": (
                "You are a reflection agent. Review the work completed in previous steps, "
                "identify what went well, what could be improved, and provide actionable "
                "insights. Return ONLY valid JSON with keys: assessment (string), "
                "strengths (list), improvements (list), score (0.0-1.0). No markdown."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Reflection task: {label}\n"
                f"Work to reflect on:\n{context}"
            ),
        },
    ]


def _build_tool_prompt(
    label: str, data: dict[str, Any], parent_outputs: dict[str, Any]
) -> list[dict[str, str]]:
    tool_name = data.get("tool", label)
    context = _format_parent_outputs(parent_outputs)
    return [
        {
            "role": "system",
            "content": (
                f"You are a tool execution agent for the tool: {tool_name}. "
                "Based on the input context, describe what the tool would do and "
                "simulate its output. Return ONLY valid JSON with keys: tool (string), "
                "input_received (string), output (string), success (bool). No markdown."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Tool: {tool_name}\n"
                f"Input context:\n{context}"
            ),
        },
    ]


def _build_memory_prompt(
    label: str, data: dict[str, Any], parent_outputs: dict[str, Any]
) -> list[dict[str, str]]:
    action = data.get("action", "retrieve")
    context = _format_parent_outputs(parent_outputs)
    return [
        {
            "role": "system",
            "content": (
                f"You are a memory management node. Perform a '{action}' operation. "
                "Return ONLY valid JSON with keys: action (string), "
                "context_retrieved (string or null), context_stored (string or null), "
                "relevance_score (0.0-1.0). No markdown."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Memory task: {label}\n"
                f"Available context:\n{context}"
            ),
        },
    ]


def _build_execution_prompt(
    label: str, data: dict[str, Any], parent_outputs: dict[str, Any]
) -> list[dict[str, str]]:
    context = _format_parent_outputs(parent_outputs)
    return [
        {
            "role": "system",
            "content": (
                "You are a code execution agent. Based on the task description and context, "
                "describe what code or commands would be executed and their expected output. "
                "Return ONLY valid JSON with keys: code_description (string), "
                "expected_output (string), exit_code (int). No markdown."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Execution task: {label}\n"
                f"Input context:\n{context}"
            ),
        },
    ]


PROMPT_BUILDERS: dict[str, Any] = {
    "planner": _build_planner_prompt,
    "supervisor": _build_supervisor_prompt,
    "agent": _build_agent_prompt,
    "decision": _build_decision_prompt,
    "reflection": _build_reflection_prompt,
    "tool": _build_tool_prompt,
    "memory": _build_memory_prompt,
    "execution": _build_execution_prompt,
}


def _format_parent_outputs(parent_outputs: dict[str, Any]) -> str:
    """Format parent node outputs into a readable context string."""
    if not parent_outputs:
        return "No prior context."
    parts = []
    for node_id, output in parent_outputs.items():
        parts.append(f"[{node_id}]:\n{json.dumps(output, indent=2, default=str)}")
    return "\n\n".join(parts)


def _parse_json_response(text: str) -> dict[str, Any]:
    """Try to extract a JSON object from LLM response text."""
    text = text.strip()
    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Try extracting from markdown code block
    if "```" in text:
        start = text.find("```")
        end = text.find("```", start + 3)
        if end > start:
            block = text[start + 3 : end].strip()
            if block.startswith("json"):
                block = block[4:].strip()
            try:
                return json.loads(block)
            except json.JSONDecodeError:
                pass
    # Try finding first { ... } block
    brace_start = text.find("{")
    brace_end = text.rfind("}")
    if brace_start >= 0 and brace_end > brace_start:
        try:
            return json.loads(text[brace_start : brace_end + 1])
        except json.JSONDecodeError:
            pass
    return {"raw_response": text}


# ── Main execution engine ─────────────────────────────────────────────


class WorkflowExecutionEngine:
    """Executes a workflow graph by processing nodes in topological order,
    calling the LLM for each node, and passing data between nodes."""

    def __init__(self) -> None:
        self._settings: AISettings | None = None
        self._client: OllamaClient | None = None

    def _get_client(self) -> OllamaClient:
        if self._client is None:
            self._settings = get_ai_settings()
            self._client = OllamaClient(
                base_url=self._settings.OLLAMA_BASE_URL,
                timeout=self._settings.OLLAMA_TIMEOUT,
                connect_timeout=self._settings.OLLAMA_CONNECT_TIMEOUT,
            )
        return self._client

    def _get_model(self) -> str:
        if self._settings is None:
            self._settings = get_ai_settings()
        return self._settings.DEFAULT_MODEL

    async def execute_workflow(
        self,
        nodes: list[dict[str, Any]],
        edges: list[dict[str, Any]],
        inputs: dict[str, Any] | None = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Execute a workflow graph, yielding status updates for each node.

        Yields dicts with keys:
          - type: "node_start" | "node_complete" | "node_error" | "workflow_complete"
          - node_id, status, output, duration_ms, etc.
        """
        execution_id = str(uuid.uuid4())
        start_time = time.monotonic()
        inputs = inputs or {}

        # Build adjacency: target -> list of source node IDs
        incoming: dict[str, list[str]] = {n["id"]: [] for n in nodes}
        for edge in edges:
            if edge["target"] in incoming:
                incoming[edge["target"]].append(edge["source"])

        # Topological sort
        start_nodes = [n["id"] for n in nodes if n.get("type") == "start"]
        if not start_nodes:
            start_nodes = [nid for nid, srcs in incoming.items() if not srcs]

        visited: set[str] = set()
        order: list[str] = []
        ready = list(start_nodes)
        while ready:
            nid = ready.pop(0)
            if nid in visited:
                continue
            if all(s in visited for s in incoming[nid]):
                order.append(nid)
                visited.add(nid)
                for e in edges:
                    if e["source"] == nid and e["target"] not in visited:
                        ready.append(e["target"])

        node_map = {n["id"]: n for n in nodes}
        parent_outputs: dict[str, Any] = {}  # node_id -> parsed output
        node_results: list[NodeResult] = []
        model = self._get_model()

        for node_id in order:
            node = node_map.get(node_id)
            if not node:
                continue

            node_type = node.get("type", "agent")
            label = node.get("label", node_id)
            data = node.get("data", {})

            # Yield node_start
            yield {
                "type": "node_start",
                "node_id": node_id,
                "node_type": node_type,
                "label": label,
            }

            # Start nodes and end nodes are metadata-only
            if node_type == "start":
                result = NodeResult(
                    node_id=node_id,
                    node_type=node_type,
                    label=label,
                    status="completed",
                    output={"message": "Workflow started", "inputs": inputs},
                )
                parent_outputs[node_id] = result.output
                node_results.append(result)
                yield {
                    "type": "node_complete",
                    **_result_to_dict(result),
                }
                continue

            if node_type == "end":
                result = NodeResult(
                    node_id=node_id,
                    node_type=node_type,
                    label=label,
                    status="completed",
                    output={"message": "Workflow completed"},
                )
                parent_outputs[node_id] = result.output
                node_results.append(result)
                yield {
                    "type": "node_complete",
                    **_result_to_dict(result),
                }
                continue

            # Build prompt for LLM-based nodes
            builder = PROMPT_BUILDERS.get(node_type)
            if not builder:
                # Unknown node type — skip LLM, mark completed
                result = NodeResult(
                    node_id=node_id,
                    node_type=node_type,
                    label=label,
                    status="completed",
                    output={"message": f"Node type '{node_type}' executed (no LLM handler)"},
                )
                parent_outputs[node_id] = result.output
                node_results.append(result)
                yield {
                    "type": "node_complete",
                    **_result_to_dict(result),
                }
                continue

            # Gather outputs from parent nodes
            parent_node_outputs = {
                src_id: parent_outputs.get(src_id, {})
                for src_id in incoming.get(node_id, [])
                if src_id in parent_outputs
            }

            messages = builder(label, data, parent_node_outputs)

            # Call LLM
            t0 = time.monotonic()
            try:
                client = self._get_client()
                response = await client.generate(
                    model=model,
                    messages=messages,
                    stream=False,
                    temperature=self._settings.TEMPERATURE if self._settings else 0.7,
                    top_p=self._settings.TOP_P if self._settings else 0.9,
                    top_k=self._settings.TOP_K if self._settings else 40,
                    max_tokens=self._settings.MAX_RESPONSE_TOKENS if self._settings else 2048,
                )

                # Extract content from Ollama response
                content = ""
                tokens_used = 0
                if isinstance(response, dict):
                    msg = response.get("message", {})
                    content = msg.get("content", "") if isinstance(msg, dict) else ""
                    tokens_used = response.get("eval_count", 0) or response.get("prompt_eval_count", 0) or 0

                parsed = _parse_json_response(content)
                duration_ms = int((time.monotonic() - t0) * 1000)

                result = NodeResult(
                    node_id=node_id,
                    node_type=node_type,
                    label=label,
                    status="completed",
                    output=parsed,
                    duration_ms=duration_ms,
                    llm_model=model,
                    tokens_used=tokens_used,
                )

            except Exception as exc:
                duration_ms = int((time.monotonic() - t0) * 1000)
                logger.error("Node %s failed: %s", node_id[:8], exc)
                result = NodeResult(
                    node_id=node_id,
                    node_type=node_type,
                    label=label,
                    status="failed",
                    output={},
                    duration_ms=duration_ms,
                    error=str(exc),
                )

            parent_outputs[node_id] = result.output
            node_results.append(result)

            if result.status == "failed":
                yield {
                    "type": "node_error",
                    **_result_to_dict(result),
                }
            else:
                yield {
                    "type": "node_complete",
                    **_result_to_dict(result),
                }

        total_ms = int((time.monotonic() - start_time) * 1000)
        all_completed = all(r.status == "completed" for r in node_results)

        yield {
            "type": "workflow_complete",
            "execution_id": execution_id,
            "status": "completed" if all_completed else "failed",
            "total_duration_ms": total_ms,
            "nodes_executed": len(node_results),
            "final_output": parent_outputs.get(order[-1], {}) if order else {},
        }


def _result_to_dict(result: NodeResult) -> dict[str, Any]:
    return {
        "node_id": result.node_id,
        "node_type": result.node_type,
        "label": result.label,
        "status": result.status,
        "output": result.output,
        "duration_ms": result.duration_ms,
        "error": result.error,
        "llm_model": result.llm_model,
        "tokens_used": result.tokens_used,
    }
