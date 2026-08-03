from pathlib import Path
from py_mono.config import WORKSPACE_ROOT, ADDITIONAL_ALLOWED_PATHS

def resolve_safe_path(user_path: str) -> Path:
    """
    Resolve a user-provided path safely inside the workspace (or an explicitly
    configured additional allowed directory).

    Prevents directory traversal (e.g., ../../etc/passwd), sibling-directory
    string-prefix collisions (e.g. /workspace vs /workspace_evil), and
    symlink-based escapes, using real path containment (Path.is_relative_to)
    instead of a string prefix check. Path.resolve() follows symlinks before
    the containment check runs, so a symlink pointing outside every allowed
    root is rejected too.
    """
    path = (WORKSPACE_ROOT / user_path).resolve()
    allowed_roots = [WORKSPACE_ROOT] + ADDITIONAL_ALLOWED_PATHS

    if not any(path.is_relative_to(root) for root in allowed_roots):
        raise ValueError(f"Access denied: {user_path} is outside allowed directories")

    return path
