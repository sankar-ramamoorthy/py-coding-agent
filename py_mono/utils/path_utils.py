from pathlib import Path
from py_mono.config import WORKSPACE_ROOT

def resolve_safe_path(user_path: str) -> Path:
    """
    Resolve a user-provided path safely inside the workspace.

    Prevents directory traversal (e.g., ../../etc/passwd).
    """
    path = (WORKSPACE_ROOT / user_path).resolve()

    if not str(path).startswith(str(WORKSPACE_ROOT)):
        raise ValueError(f"Access denied: {user_path} is outside workspace")

    return path
