"""Database MCP tool for database operations."""

import asyncio
from typing import Any

from app.tools.base import BaseTool
from app.tools.schemas import (
    ToolCapability,
    ToolHealth,
    ToolProvider,
    ToolStatus,
)
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class DatabaseTool(BaseTool):
    """Database tool for SQL operations.

    Capabilities:
    - Execute Query
    - List Tables
    - Describe Table
    - Execute DDL
    """

    def __init__(self):
        """Initialize database tool."""
        super().__init__(
            tool_id="database",
            name="Database",
            description="Database query execution and schema inspection",
            provider=ToolProvider.MCP,
            version="1.0.0",
            capabilities=[
                ToolCapability(
                    name="execute_query",
                    description="Execute a SQL query",
                    operations=["query"],
                    required_permissions=[],
                ),
                ToolCapability(
                    name="list_tables",
                    description="List all tables",
                    operations=["list"],
                    required_permissions=[],
                ),
                ToolCapability(
                    name="describe_table",
                    description="Describe table schema",
                    operations=["describe"],
                    required_permissions=[],
                ),
                ToolCapability(
                    name="execute_ddl",
                    description="Execute DDL statement",
                    operations=["ddl"],
                    required_permissions=[],
                ),
            ],
            supported_operations=["query", "list", "describe", "ddl"],
        )
        self._engine = None

    async def _get_engine(self):
        """Get database engine."""
        if self._engine is None:
            from sqlalchemy.ext.asyncio import create_async_engine
            settings = get_settings()
            self._engine = create_async_engine(settings.DATABASE_URL, echo=False)
        return self._engine

    async def health_check(self) -> ToolHealth:
        """Check database tool health."""
        try:
            from sqlalchemy import text
            engine = await self._get_engine()
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return ToolHealth(
                status=ToolStatus.HEALTHY,
                latency_ms=0.0,
                version=self.version,
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
        """Validate database request."""
        base_valid, base_error = await super().validate(operation, parameters)
        if not base_valid:
            return base_valid, base_error

        if operation == "query" and "sql" not in parameters:
            return False, "Missing required parameter: sql"

        if operation == "describe" and "table_name" not in parameters:
            return False, "Missing required parameter: table_name"

        if operation == "ddl" and "sql" not in parameters:
            return False, "Missing required parameter: sql"

        return True, None

    async def execute(
        self,
        operation: str,
        parameters: dict[str, Any],
        request_id: str,
    ) -> dict[str, Any]:
        """Execute database operation."""
        self._active_requests[request_id] = True

        try:
            if operation == "query":
                return await self._execute_query(parameters)
            elif operation == "list":
                return await self._list_tables()
            elif operation == "describe":
                return await self._describe_table(parameters)
            elif operation == "ddl":
                return await self._execute_ddl(parameters)
            else:
                return {"success": False, "error": f"Unknown operation: {operation}"}
        finally:
            self._active_requests.pop(request_id, None)

    async def _execute_query(self, params: dict[str, Any]) -> dict[str, Any]:
        """Execute a SQL query."""
        from sqlalchemy import text

        sql = params["sql"]
        limit = params.get("limit", 100)

        try:
            engine = await self._get_engine()
            async with engine.connect() as conn:
                result = await conn.execute(text(sql))
                rows = result.fetchmany(limit)
                columns = result.keys() if rows else []
                return {
                    "success": True,
                    "columns": list(columns),
                    "rows": [list(row) for row in rows],
                    "row_count": len(rows),
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _list_tables(self) -> dict[str, Any]:
        """List all tables."""
        from sqlalchemy import text

        try:
            engine = await self._get_engine()
            async with engine.connect() as conn:
                result = await conn.execute(text(
                    "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
                ))
                tables = [row[0] for row in result]
                return {
                    "success": True,
                    "tables": tables,
                    "count": len(tables),
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _describe_table(self, params: dict[str, Any]) -> dict[str, Any]:
        """Describe table schema."""
        from sqlalchemy import text

        table_name = params["table_name"]

        try:
            engine = await self._get_engine()
            async with engine.connect() as conn:
                result = await conn.execute(text(
                    "SELECT column_name, data_type, is_nullable, column_default "
                    "FROM information_schema.columns WHERE table_name = :table_name"
                ), {"table_name": table_name})
                columns = [
                    {
                        "name": row[0],
                        "type": row[1],
                        "nullable": row[2] == "YES",
                        "default": row[3],
                    }
                    for row in result
                ]
                return {
                    "success": True,
                    "table": table_name,
                    "columns": columns,
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _execute_ddl(self, params: dict[str, Any]) -> dict[str, Any]:
        """Execute DDL statement."""
        from sqlalchemy import text

        sql = params["sql"]

        try:
            engine = await self._get_engine()
            async with engine.connect() as conn:
                await conn.execute(text(sql))
                await conn.commit()
                return {
                    "success": True,
                    "message": "DDL executed successfully",
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def cleanup(self) -> None:
        """Clean up database tool."""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
        await super().cleanup()
