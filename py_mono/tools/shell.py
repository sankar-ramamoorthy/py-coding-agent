# py_mono/tools/shell.py
from py_mono.tools.tool import Tool
from py_mono.config import WORKSPACE_ROOT
import subprocess
from pathlib import Path

def run_shell(command):
    """
    Execute a shell command in the workspace.

    Args:
        command (str): Shell command to run

    Returns:
        str: stdout + stderr or actionable error messages
    """
    if not command or command.strip() == "":
        return "[TOOL ERROR] No command provided."

    # security check
    FORBIDDEN = ["rm -rf /", "shutdown", "reboot"]
    if any(bad in command for bad in FORBIDDEN):
        return "[SECURITY] Command blocked"

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=str(WORKSPACE_ROOT)
        )
        output = result.stdout + result.stderr
        # Optional: truncate very long output for LLM readability
        if len(output) > 10000:
            output = output[:10000] + "\n[OUTPUT TRUNCATED]"
        return output

    except Exception as e:
        return f"[TOOL ERROR] Failed to execute command: {str(e)}"


shell_tool = Tool(
    name="shell",
    description="Run a shell command in the workspace and return stdout + stderr. Blocks dangerous commands.",
    func=run_shell,
    parameters={
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The shell command to execute"
            }
        },
        "required": ["command"]
    }
)