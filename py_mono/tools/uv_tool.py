# py_mono/tools/uv_tool.py

import subprocess
from py_mono.tools.tool import Tool


def install_package(package_name: str) -> str:
    """
    Install a Python package using uv.

    Args:
        package_name (str): Name of the package to install

    Returns:
        str: Success or error message
    """
    if not package_name or not package_name.strip():
        return "[TOOL ERROR] No package name provided."

    try:
        result = subprocess.run(
            ["uv", "pip", "install", "--system", package_name],
            capture_output=True,
            text=True
        )
        output = (result.stdout + result.stderr).strip()
        if result.returncode == 0:
            return f"✅ Successfully installed {package_name}\n{output}"
        else:
            return f"[TOOL ERROR] Failed to install {package_name}\n{output}"

    except FileNotFoundError:
        return "[TOOL ERROR] uv not found. Is it installed in the container?"
    except Exception as e:
        return f"[TOOL ERROR] {str(e)}"


uv_tool = Tool(
    name="install_package",
    description="Install a Python package using uv inside the Docker container",
    func=install_package,
    parameters={
        "type": "object",
        "properties": {
            "package_name": {
                "type": "string",
                "description": "Name of the Python package to install (e.g. 'pandas', 'requests')"
            }
        },
        "required": ["package_name"]
    }
)