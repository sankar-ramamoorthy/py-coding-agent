#py_mono\tools\shell.py
from py_mono.tools.tool import Tool
import subprocess

def run_shell(command):
    result = subprocess.run(
        command, shell=True, capture_output=True, text=True
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