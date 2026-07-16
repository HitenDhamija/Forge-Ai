"""Browser MCP tool for web operations."""

import httpx
from typing import Any

from app.tools.base import BaseTool
from app.tools.schemas import (
    ToolCapability,
    ToolHealth,
    ToolProvider,
    ToolStatus,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class BrowserTool(BaseTool):
    """Browser tool for web operations.

    Capabilities:
    - Fetch URL
    - Search Web
    - Get Page Content
    """

    def __init__(self):
        """Initialize browser tool."""
        super().__init__(
            tool_id="browser",
            name="Browser",
            description="Web browsing and content extraction",
            provider=ToolProvider.MCP,
            version="1.0.0",
            capabilities=[
                ToolCapability(
                    name="fetch_url",
                    description="Fetch URL content",
                    operations=["fetch"],
                    required_permissions=[],
                ),
                ToolCapability(
                    name="search_web",
                    description="Search the web",
                    operations=["search"],
                    required_permissions=[],
                ),
                ToolCapability(
                    name="get_page_content",
                    description="Get page content as text",
                    operations=["content"],
                    required_permissions=[],
                ),
            ],
            supported_operations=["fetch", "search", "content"],
        )
        self._client = httpx.AsyncClient(timeout=30)

    async def health_check(self) -> ToolHealth:
        """Check browser tool health."""
        try:
            response = await self._client.get("https://httpbin.org/get")
            if response.status_code == 200:
                return ToolHealth(
                    status=ToolStatus.HEALTHY,
                    latency_ms=0.0,
                    version=self.version,
                )
            return ToolHealth(
                status=ToolStatus.ERROR,
                error_message="HTTP request failed",
            )
        except Exception as e:
            return ToolHealth(
                status=ToolStatus.ERROR,
                error_message=str(e),
            )

    async def validate(
        self,
        operation: str,
        parameters: dict[str, Any],
    ) -> tuple[bool, str | None]:
        """Validate browser request."""
        base_valid, base_error = await super().validate(operation, parameters)
        if not base_valid:
            return base_valid, base_error

        if operation == "fetch" and "url" not in parameters:
            return False, "Missing required parameter: url"

        if operation == "search" and "query" not in parameters:
            return False, "Missing required parameter: query"

        return True, None

    async def execute(
        self,
        operation: str,
        parameters: dict[str, Any],
        request_id: str,
    ) -> dict[str, Any]:
        """Execute browser operation."""
        self._active_requests[request_id] = True

        try:
            if operation == "fetch":
                return await self._fetch_url(parameters)
            elif operation == "search":
                return await self._search_web(parameters)
            elif operation == "content":
                return await self._get_content(parameters)
            else:
                return {"success": False, "error": f"Unknown operation: {operation}"}
        finally:
            self._active_requests.pop(request_id, None)

    async def _fetch_url(self, params: dict[str, Any]) -> dict[str, Any]:
        """Fetch URL content."""
        url = params["url"]
        try:
            response = await self._client.get(url)
            return {
                "success": response.status_code == 200,
                "status_code": response.status_code,
                "content": response.text[:5000] if response.status_code == 200 else None,
                "error": None if response.status_code == 200 else f"HTTP {response.status_code}",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _search_web(self, params: dict[str, Any]) -> dict[str, Any]:
        """Search the web."""
        query = params["query"]
        try:
            url = f"https://html.duckduckgo.com/html/?q={query}"
            response = await self._client.get(url)
            return {
                "success": response.status_code == 200,
                "content": response.text[:5000] if response.status_code == 200 else None,
                "error": None if response.status_code == 200 else "Search failed",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _get_content(self, params: dict[str, Any]) -> dict[str, Any]:
        """Get page content."""
        url = params["url"]
        try:
            response = await self._client.get(url)
            if response.status_code == 200:
                from html.parser import HTMLParser

                class TextExtractor(HTMLParser):
                    def __init__(self):
                        super().__init__()
                        self.text = []
                        self.skip = False

                    def handle_starttag(self, tag, attrs):
                        if tag in ("script", "style"):
                            self.skip = True

                    def handle_endtag(self, tag):
                        if tag in ("script", "style"):
                            self.skip = False

                    def handle_data(self, data):
                        if not self.skip:
                            self.text.append(data.strip())

                extractor = TextExtractor()
                extractor.feed(response.text)
                content = " ".join(filter(None, extractor.text))
                return {
                    "success": True,
                    "content": content[:5000],
                    "url": url,
                }
            return {
                "success": False,
                "error": f"HTTP {response.status_code}",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def cleanup(self) -> None:
        """Clean up browser tool."""
        await self._client.aclose()
        await super().cleanup()
