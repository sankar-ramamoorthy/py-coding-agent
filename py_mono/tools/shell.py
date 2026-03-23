# py_mono/tools/shell.py

import subprocess
from py_mono.tools.tool import Tool
from py_mono.config import WORKSPACE_ROOT

FORBIDDEN_PATTERNS = [
    "rm -rf /",
    "rm -rf ~",
    "rm -rf $home",
    ":(){:|:&};:",
    "sudo",
    "su ",
    "chmod 777 /",
    "curl | bash",
    "curl | sh",
    "wget | bash",
    "wget | sh",
    "shutdown",
    "reboot",
    "mkfs",
    "dd if=",
]

def is_forbidden(command: str) -> bool:
    cmd = command.strip().lower()
    return any(pattern in cmd for pattern in FORBIDDEN_PATTERNS)


def run_shell(command: str) -> str:
    """
    Execute a shell command inside the workspace.

    Args:
        command (str): Shell command to run

    Returns:
        str: stdout + stderr output, or actionable error message
    """
    if not command or not command.strip():
        return "[TOOL ERROR] No command provided."

    if is_forbidden(command):
        return f"[SECURITY] Command blocked: '{command}'"

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=str(WORKSPACE_ROOT)
        )
        output = (result.stdout + result.stderr).strip()

        if len(output) > 10000:
            output = output[:10000] + "\n[OUTPUT TRUNCATED]"

        if not output:
            return f"✅ Command completed with no output (exit code {result.returncode})"

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