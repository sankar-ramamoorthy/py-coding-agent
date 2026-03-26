# py_mono/mcp/mcp_client.py
"""
Thin async FastMCP client wrapper.

Provides a single generic function for calling any tool
on any FastMCP server by URL.

Usage:
    result = await call_mcp_tool(
        url="http://datetime-mcp:50051/mcp",
        tool_name="get_current_datetime_tool",
        args={}
    )
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

try:
    from fastmcp import Client
except ImportError:
    raise ImportError(
        "fastmcp is not installed. "
        "Add 'fastmcp' to pyproject.toml dependencies."
    )


async def call_mcp_tool(url: str, tool_name: str, args: dict = None) -> Any:
    """
    Call a tool on a FastMCP server.

    Args:
        url (str): Full MCP server URL e.g. http://datetime-mcp:50051/mcp
        tool_name (str): Name of the tool to call
        args (dict): Tool arguments (default: empty dict)

    Returns:
        Any: Tool result — structured_content if available, else raw content

    Raises:
        Exception: If the MCP server is unreachable or the tool call fails
    """
    args = args or {}

    logger.debug(f"Calling MCP tool '{tool_name}' at {url} with args {args}")

    async with Client(url) as client:
        result = await client.call_tool(tool_name, args)
        return result.structured_content or result.content