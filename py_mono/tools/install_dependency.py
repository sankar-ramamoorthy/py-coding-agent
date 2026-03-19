from py_mono.tools.read_file import Tool
import subprocess
import sys

def install_dependency(package):
    subprocess.run(
        [sys.executable, "-m", "uv", "pip", "install", package],
        check=True
    )
    return f"Installed {package}"

install_dep_tool = Tool(
    "install_dependency",
    "Install Python dependency using uv",
    install_dependency
)
