# py_mono/mcp/mcp_tool.py
"""
Sync bridge and Tool definitions for MCP servers.

Since agent.py is synchronous but FastMCP client calls are async,
this module provides sync wrappers using asyncio.run().

Each MCP server gets a sync wrapper function and a Tool definition.
The agent treats MCP tools identically to built-in tools.

See ADR-004 for architecture details.
"""

import asyncio
import logging
import os
from py_mono.tools.tool import Tool
from py_mono.mcp.mcp_client import call_mcp_tool

logger = logging.getLogger(__name__)

# ----------------------------
# MCP Server URLs
# ----------------------------
# Read from environment with sensible Docker Compose defaults.
# Service names match docker-compose.yml service names.

DATETIME_MCP_URL = os.getenv(
    "DATETIME_MCP_URL",
    "http://datetime-mcp:50051/mcp"
)


# ----------------------------
# Sync bridge helpers
# ----------------------------

def _run_async(coro):
    """Run an async coroutine synchronously."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If already inside an event loop (e.g. tests), create a new one
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result()
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


# ----------------------------
# Datetime MCP Tool
# ----------------------------

def get_current_datetime() -> str:
    """
    Get current UTC datetime from the datetime MCP server.

    Returns:
        str: Current UTC datetime as ISO 8601 string, or error message
    """
    try:
        result = _run_async(
            call_mcp_tool(
                url=DATETIME_MCP_URL,
                tool_name="get_current_datetime_tool",
                args={}
            )
        )
        return str(result)
    except Exception as e:
        logger.error(f"datetime-mcp call failed: {e}")
        return f"[MCP ERROR] Could not reach datetime-mcp: {str(e)}"


datetime_mcp_tool = Tool(
    name="get_current_datetime",
    description="Get the current UTC date and time from the datetime MCP server.",
    func=get_current_datetime,
    parameters={
        "type": "object",
        "properties": {},
        "required": []
    }
)