"""
Main entry point for py-coding-agent V1.

Features:
- Loads base tools and dynamic tools
- Connects to host Ollama LLM
- Starts CLI for user interaction
"""

from py_mono.agent.agent import Agent
from py_mono.llm.ollama_provider import OllamaProvider
from py_mono.tools.read_file import read_tool
from py_mono.tools.write_file import write_tool
from py_mono.tools.edit_file import edit_tool
from py_mono.tools.shell import shell_tool
from py_mono.tools.uv_tool import uv_tool
from py_mono.tools.create_tool import create_tool_tool
from py_mono.tools.list_files import list_files_tool

from py_mono.tools.tool_loader import load_dynamic_tools
from py_mono.ui.cli import start_cli

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
        list_files_tool
    ]

    # Load dynamic tools from dynamic_tools folder
    dynamic_tools = load_dynamic_tools()

    # Combine all tools
    tools = base_tools + dynamic_tools

    # Initialize OllamaProvider (host connection)
    llm = OllamaProvider()  # reads OLLAMA_BASE_URL and OLLAMA_MODEL from environment

    # Create the agent
    agent = Agent(llm, tools)

    # Start the CLI
    start_cli(agent)

if __name__ == "__main__":
    main()