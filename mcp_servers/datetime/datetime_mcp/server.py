# mcp_servers/datetime/datetime_mcp/server.py
"""
FastMCP datetime server.

Exposes a single tool:
    get_current_datetime_tool — returns current UTC datetime as ISO 8601 string

Runs HTTP transport on port 50051.
Accessible from agent container at http://datetime-mcp:50051/mcp
"""

import logging
from fastmcp import FastMCP
from datetime_mcp.tool import current_datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("datetime-mcp")


def main():
    mcp = FastMCP("datetime-mcp")

    @mcp.tool
    def get_current_datetime_tool() -> str:
        """Return current UTC datetime as ISO 8601 string."""
        return current_datetime()

    logger.info("Starting datetime-mcp on http://0.0.0.0:50051/mcp")
    mcp.run(transport="http", host="0.0.0.0", port=50051)


if __name__ == "__main__":
    main()