from py_mono.tools.tool import Tool

def install_package(package_name):
    # For now, stub function, replace with uv logic later
    return f"Simulated installing package: {package_name}"

uv_tool = Tool(
    "install_package",
    "Install a Python package using uv (stub)",
    install_package
)