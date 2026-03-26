# mcp_servers/datetime/datetime_mcp/tool.py
"""
Core datetime business logic.
Returns current UTC datetime as ISO 8601 string.
"""

from datetime import datetime, timezone


def current_datetime() -> str:
    """Return current UTC date and time as ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()