# py_mono/tools/shell.py

import subprocess
from py_mono.tools.tool import Tool
from py_mono.config import WORKSPACE_ROOT

DEFAULT_SHELL_TIMEOUT_SECONDS = 30

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
            cwd=str(WORKSPACE_ROOT),
            timeout=DEFAULT_SHELL_TIMEOUT_SECONDS,
        )
        output = (result.stdout + result.stderr).strip()

        if len(output) > 10000:
            output = output[:10000] + "\n[OUTPUT TRUNCATED]"

        if not output:
            return f"✅ Command completed with no output (exit code {result.returncode})"

        return output

    except subprocess.TimeoutExpired:
        return f"[TOOL ERROR] Command timed out after {DEFAULT_SHELL_TIMEOUT_SECONDS}s: '{command}'"
    except Exception as e:
        return f"[TOOL ERROR] Failed to execute command: {str(e)}"


shell_tool = Tool(
    name="shell",
    description=(
        "Run a shell command in the workspace and return stdout + stderr. "
        "Blocks a small set of known-dangerous command patterns as defense-in-depth only — "
        "this is NOT a security boundary and does not sandbox command content "
        "(e.g. 'cat /etc/passwd' is not blocked). Only enable and use in a trusted environment. "
        f"Commands are terminated after {DEFAULT_SHELL_TIMEOUT_SECONDS}s if still running."
    ),
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