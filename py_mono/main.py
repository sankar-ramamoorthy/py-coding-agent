# py_mono/main.py
"""
Main entry point for py-coding-agent V1.

Loads base tools, dynamic tools, and MCP tools.
Initializes the LLM provider based on LLM_PROVIDER environment variable.
Starts the CLI.

Environment Variables:
    LLM_PROVIDER        — 'ollama' (default) or 'litellm'
    OLLAMA_MODEL        — model name for Ollama
    LITELLM_MODEL       — model string for LiteLLM (e.g. groq/qwen/qwen3-32b)
    GROQ_API_KEY        — if using Groq via LiteLLM
    DATETIME_MCP_URL    — datetime MCP server URL (default: http://datetime-mcp:50051/mcp)
"""


from typing import Optional

from py_mono.config import LLM_PROVIDER, ENABLE_SHELL_TOOL, ENABLE_DYNAMIC_TOOLS
from py_mono.agent.agent import Agent
from py_mono.session.session_manager import SessionManager
from py_mono.tools.read_file import read_tool
from py_mono.tools.write_file import write_tool
from py_mono.tools.edit_file import edit_tool
from py_mono.tools.shell import shell_tool
from py_mono.tools.uv_tool import uv_tool
from py_mono.tools.create_tool import create_tool_tool
from py_mono.tools.list_files import list_files_tool
from py_mono.tools.tool_loader import load_dynamic_tools
from py_mono.ui.cli import start_cli

# Optional: if you want env‑only for now, this can be None
from py_mono.security.key_manager import KeyManager
import os
from py_mono.skill.base import SkillRegistry


#deleted init_provider() entirely; 
# it’s now replaced by REGISTRY + SessionManager


def load_mcp_tools() -> list:
    """
    Load MCP-backed tools.

    Each tool is a sync wrapper around an async FastMCP client call.
    Returns empty list gracefully if MCP tools fail to import.

    Returns:
        list: List of Tool instances backed by MCP servers
    """
    try:
        #from py_mono.mcp.mcp_tool import datetime_mcp_tool
        from py_mono.mcp_integration.mcp_tool import datetime_mcp_tool
        tools = [datetime_mcp_tool]
        print(f"🔌 Loaded {len(tools)} MCP tool(s): {[t.name for t in tools]}")
        return tools
    except Exception as e:
        import traceback
        traceback.print_exc()  # ← add this
        print(f"⚠️  MCP tools unavailable: {e}")
        return []
 
def load_skills() -> SkillRegistry:
    """
    Load and return the SkillRegistry.
    Scans skills/ directory at project root.
    """
    registry = SkillRegistry()
    registry.load()
    skills = registry.list_skills()
    if skills:
        names = [s["name"] for s in skills]
        print(f"🎯 Loaded {len(skills)} skill(s): {names}")
    else:
        print("🎯 No skills found (skills/ directory empty or missing).")
    return registry


def build_base_tools(enable_shell: Optional[bool] = None) -> list:
    """
    Assemble the base (always-available-unless-gated) tool set.

    The shell tool is opt-in: it is included only when ENABLE_SHELL_TOOL is
    truthy in the environment (or when enable_shell is explicitly passed,
    which overrides the environment — used by tests to avoid module-reload
    fragility). All other base tools are unconditional, as before.
    """
    tools = [
        read_tool,
        write_tool,
        edit_tool,
        uv_tool,
        create_tool_tool,
        list_files_tool,
    ]
    effective_enable_shell = enable_shell if enable_shell is not None else ENABLE_SHELL_TOOL
    if effective_enable_shell:
        tools.append(shell_tool)
    return tools


def main():
    # Base tools
    base_tools = build_base_tools()

    # Dynamic tools — off by default; ENABLE_DYNAMIC_TOOLS must be explicitly
    # set (ISS-003: LLM-generated code executes on load, not a full sandbox)
    if ENABLE_DYNAMIC_TOOLS:
        dynamic_tools = load_dynamic_tools()
        if dynamic_tools:
            print(f"🔧 Loaded {len(dynamic_tools)} dynamic tool(s): {[t.name for t in dynamic_tools]}")
    else:
        dynamic_tools = []
        print("🔒 Dynamic tools disabled (ENABLE_DYNAMIC_TOOLS=false)")

    # MCP tools
    mcp_tools = load_mcp_tools()

    skill_registry = load_skills()
    # Combined tools
    tools = base_tools + dynamic_tools + mcp_tools

    # KeyManager: create only if LLM_MASTER_KEY is set
    key_manager: Optional[KeyManager] = None
    if os.getenv("LLM_MASTER_KEY"):
        key_manager = KeyManager()
        print(f"🔐 KeyManager loaded with {len(key_manager.list_providers())} stored keys.")

    # Initialize session manager with default provider from env
    session_manager = SessionManager(
        default_provider=LLM_PROVIDER,
        key_manager=key_manager,
    )

    # Create agent
    agent = Agent(
        session_manager,
        tools,
        skill_registry,
        dynamic_tool_names={t.name for t in dynamic_tools},
        dynamic_tools_folder="dynamic_tools",
        non_dynamic_tools=base_tools + mcp_tools,
    )

    # Start CLI
    start_cli(agent)


if __name__ == "__main__":
    main()

