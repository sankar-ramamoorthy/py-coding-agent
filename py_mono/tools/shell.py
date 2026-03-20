#py_mono\tools\shell.py
from py_mono.tools.tool import Tool
import subprocess

from py_mono.config import WORKSPACE_ROOT

def run_shell(command):
    FORBIDDEN = ["rm -rf /", "shutdown", "reboot"]

    if any(bad in command for bad in FORBIDDEN):
        return "[SECURITY] Command blocked"

    result = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True,
        cwd=str(WORKSPACE_ROOT)  
    )
    return result.stdout + result.stderr



shell_tool = Tool(
    name="shell",
    description="Run a shell command and return stdout + stderr.",
    func=run_shell,
    parameters={
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The shell command to execute."
            }
        },
        "required": ["command"]
    }
)

