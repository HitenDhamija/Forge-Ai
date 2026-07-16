"""Researcher agent for gathering information and knowledge."""

from typing import Any

from app.agents.agent_base import AgentBase
from app.agents.schemas import AgentType
from app.agents.tools.registry import ToolRegistry
from app.core.logging import get_logger

logger = get_logger(__name__)


class ResearcherAgent(AgentBase):
    """Agent specialized in research and information gathering.

    The Researcher Agent explores codebases, documentation, and external
    resources to gather information needed for other agents or tasks.
    """

    def __init__(self, tool_registry: ToolRegistry) -> None:
        super().__init__(
            name="Researcher Agent",
            description="Researches codebase, documentation, and external resources",
            agent_type=AgentType.RESEARCHER,
            tool_registry=tool_registry,
        )

    async def execute(self, task_id: str, **kwargs: Any) -> dict[str, Any]:
        """Execute research task.

        Args:
            task_id: ID of the task.
            **kwargs: Must contain 'topic' or 'query' field.

        Returns:
            Research results with findings and sources.
        """
        topic = kwargs.get("topic") or kwargs.get("query", "")
        context = kwargs.get("context", {})
        scope = kwargs.get("scope", "local")

        logger.info("Researching task %s: %s", task_id, topic[:100])

        research_result = {
            "topic": topic,
            "scope": scope,
            "findings": [],
            "sources": [],
            "summary": "",
        }

        if scope == "local" or scope == "codebase":
            codebase_results = await self._research_codebase(topic, context)
            research_result["findings"].extend(codebase_results.get("findings", []))
            research_result["sources"].extend(codebase_results.get("sources", []))

        if scope == "local" or scope == "documentation":
            doc_results = await self._research_documentation(topic, context)
            research_result["findings"].extend(doc_results.get("findings", []))
            research_result["sources"].extend(doc_results.get("sources", []))

        if scope == "analysis":
            analysis_results = await self._analyze_topic(topic, context)
            research_result["findings"].extend(analysis_results.get("findings", []))

        research_result["summary"] = self._generate_summary(
            topic,
            research_result["findings"],
        )

        return research_result

    async def _research_codebase(
        self, topic: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        """Research within the codebase."""
        findings = []
        sources = []

        search_patterns = self._generate_search_patterns(topic)

        for pattern in search_patterns[:3]:
            result = await self.tool_registry.execute_tool(
                "grep_search",
                agent_id=self.id,
                pattern=pattern,
                directory=context.get("directory", "."),
                max_results=20,
            )

            if result.get("success") and result.get("results"):
                for match in result["results"]:
                    findings.append({
                        "type": "code_match",
                        "file": match.get("file"),
                        "line": match.get("line_number"),
                        "content": match.get("line"),
                        "pattern": pattern,
                    })
                    if match.get("file") not in sources:
                        sources.append(match.get("file"))

        return {
            "findings": findings,
            "sources": sources,
        }

    async def _research_documentation(
        self, topic: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        """Research documentation files."""
        findings = []
        sources = []

        doc_patterns = ["*.md", "*.rst", "*.txt", "README*"]

        for pattern in doc_patterns:
            result = await self.tool_registry.execute_tool(
                "find_files",
                agent_id=self.id,
                pattern=pattern,
                directory=context.get("directory", "."),
            )

            if result.get("success") and result.get("results"):
                for file_info in result["results"]:
                    file_path = file_info.get("path", "")
                    read_result = await self.tool_registry.execute_tool(
                        "read_file",
                        agent_id=self.id,
                        file_path=file_path,
                    )

                    if read_result.get("success"):
                        content = read_result.get("content", "")
                        if self._is_relevant(content, topic):
                            findings.append({
                                "type": "documentation",
                                "file": file_path,
                                "excerpt": content[:500],
                            })
                            if file_path not in sources:
                                sources.append(file_path)

        return {
            "findings": findings,
            "sources": sources,
        }

    async def _analyze_topic(
        self, topic: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        """Analyze a topic using LLM."""
        findings = []

        prompt = f"""Research and analyze the following topic: {topic}

Provide a comprehensive analysis including:
1. Key concepts and definitions
2. Related patterns and best practices
3. Common implementation approaches
4. Potential challenges and considerations

Context: {context.get('additional_info', 'No additional context provided')}
"""

        result = await self.tool_registry.execute_tool(
            "llm_query",
            agent_id=self.id,
            prompt=prompt,
        )

        if result.get("success"):
            findings.append({
                "type": "analysis",
                "topic": topic,
                "details": result.get("response", ""),
            })

        return {
            "findings": findings,
            "sources": [],
        }

    def _generate_search_patterns(self, topic: str) -> list[str]:
        """Generate search patterns from topic."""
        words = topic.lower().split()
        patterns = []

        if len(words) >= 2:
            patterns.append("\\b".join(words))

        patterns.extend(words[:3])

        camel_case = "".join(w.capitalize() for w in words if w)
        if camel_case:
            patterns.append(camel_case)

        snake_case = "_".join(words)
        patterns.append(snake_case)

        return patterns

    def _is_relevant(self, content: str, topic: str) -> bool:
        """Check if content is relevant to the topic."""
        topic_words = set(topic.lower().split())
        content_lower = content.lower()

        matches = sum(1 for word in topic_words if word in content_lower)
        return matches >= len(topic_words) // 2

    def _generate_summary(
        self, topic: str, findings: list[dict[str, Any]]
    ) -> str:
        """Generate a summary of research findings."""
        if not findings:
            return f"No findings found for topic: {topic}"

        finding_types = {}
        for finding in findings:
            ftype = finding.get("type", "unknown")
            if ftype not in finding_types:
                finding_types[ftype] = 0
            finding_types[ftype] += 1

        summary_parts = [f"Research on '{topic}' found {len(findings)} items:"]
        for ftype, count in finding_types.items():
            summary_parts.append(f"  - {count} {ftype} findings")

        return "\n".join(summary_parts)
