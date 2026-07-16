"""Factory for creating and configuring the tool registry."""

from app.agents.config import get_agent_settings
from app.agents.tools.ai_tools import AnalyzeCodeTool, LLMQueryTool
from app.agents.tools.file_tools import (
    EditFileTool,
    ListDirectoryTool,
    ReadFileTool,
    WriteFileTool,
)
from app.agents.tools.registry import ToolRegistry
from app.agents.tools.search_tools import FindFilesTool, GrepSearchTool
from app.core.logging import get_logger

logger = get_logger(__name__)


def create_tool_registry() -> ToolRegistry:
    """Create and configure the default tool registry.

    Returns:
        Configured ToolRegistry with all default tools registered.
    """
    registry = ToolRegistry()
    settings = get_agent_settings()

    file_tools = [
        ReadFileTool(),
        ListDirectoryTool(),
    ]

    if settings.ENABLE_FILE_MODIFICATION:
        file_tools.extend([
            WriteFileTool(),
            EditFileTool(),
        ])

    search_tools = [
        GrepSearchTool(),
        FindFilesTool(),
    ]

    ai_tools = [
        LLMQueryTool(),
        AnalyzeCodeTool(),
    ]

    for tool in file_tools + search_tools + ai_tools:
        registry.register(tool)

    logger.info("Tool registry created with %d tools", len(registry))
    return registry
