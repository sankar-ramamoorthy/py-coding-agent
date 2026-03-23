# py_mono/main.py
"""
Main entry point for py-coding-agent V1.

Loads base tools and dynamic tools, initializes the LLM provider
based on LLM_PROVIDER environment variable, and starts the CLI.

Environment Variables:
    LLM_PROVIDER    — 'ollama' (default) or 'litellm'
    OLLAMA_MODEL    — model name for Ollama
    LITELLM_MODEL   — model string for LiteLLM (e.g. groq/llama-3.3-70b-versatile)
    GROQ_API_KEY    — if using Groq via LiteLLM
"""

from py_mono.config import LLM_PROVIDER
from py_mono.agent.agent import Agent
from py_mono.tools.read_file import read_tool
from py_mono.tools.write_file import write_tool
from py_mono.tools.edit_file import edit_tool
from py_mono.tools.shell import shell_tool
from py_mono.tools.uv_tool import uv_tool
from py_mono.tools.create_tool import create_tool_tool
from py_mono.tools.list_files import list_files_tool
from py_mono.tools.tool_loader import load_dynamic_tools
from py_mono.ui.cli import start_cli


def init_provider():
    """
    Initialize the LLM provider based on LLM_PROVIDER environment variable.

    Returns:
        LLMProvider: Configured provider instance ready for use
    
    Raises:
        ValueError: If LLM_PROVIDER is set to an unsupported value
    """
    if LLM_PROVIDER == "litellm":
        print(f"🤖 Using LiteLLM provider")
        from py_mono.llm.litellm_provider import LiteLLMProvider
        return LiteLLMProvider()
    elif LLM_PROVIDER == "ollama":
        print(f"🤖 Using Ollama provider")
        from py_mono.llm.ollama_provider import OllamaProvider
        return OllamaProvider()
    else:
        raise ValueError(
            f"Unsupported LLM_PROVIDER: '{LLM_PROVIDER}'. "
            "Supported values: 'ollama', 'litellm'"
        )


def main():
    """
    Initialize the agent and start the CLI.
    """
    # Base tools
    base_tools = [
        read_tool,
        write_tool,
        edit_tool,
        shell_tool,
        uv_tool,
        create_tool_tool,
        list_files_tool,
    ]

    # Load dynamic tools from dynamic_tools folder
    dynamic_tools = load_dynamic_tools()
    if dynamic_tools:
        print(f"🔧 Loaded {len(dynamic_tools)} dynamic tool(s): {[t.name for t in dynamic_tools]}")

    # Combine all tools
    tools = base_tools + dynamic_tools

    # Initialize provider
    llm = init_provider()

    # Create the agent
    agent = Agent(llm, tools)

    # Start the CLI
    start_cli(agent)


if __name__ == "__main__":
    main()